from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from app.core.dependencies import get_note_service
from app.core.security import get_current_user
from app.notes.service import NoteService
from app.notes.schema import NoteCreate, NoteResponse
from app.models import User, NoteStatus
from app.common.pagination import PaginationParams, PaginatedResponse
from app.common.filtering import NoteFilters

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={
        400: {"description": "Bad request - malformed request or invalid data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Note not found"},
        422: {"description": "Validation error - request data doesn't meet requirements"},
        503: {"description": "Service unavailable - background processing temporarily unavailable"},
    }
)


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    note_create: NoteCreate,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Create a new note and queue it for AI summarization.

    Creates a new note with the provided content and automatically queues
    a background job for AI-powered summarization. The note starts with
    status 'queued' and will be processed asynchronously.

    - **raw_text**: The content of the note to be summarized
    - Returns: Created note with ID, timestamps, and initial status

    The AI summarization process analyzes the content and generates
    summaries based on detected keywords and content type.
    """
    return await note_service.create_note(note_create, current_user)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get a specific note by ID.

    Retrieves a note by its unique identifier. Access is controlled by user role:

    - **AGENT users**: Can only access their own notes
    - **ADMIN users**: Can access any note in the system

    Returns the note with its current processing status and summary (if available).

    Raises 404 if the note doesn't exist or the user doesn't have access to it.
    """
    return await note_service.get_note(note_id, current_user)


@router.get("/", response_model=PaginatedResponse[NoteResponse])
async def get_notes(
    # Pagination parameters
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    # Filtering parameters
    search: Optional[str] = Query(default=None, description="Search in note content and summary", min_length=1, max_length=100),
    status: Optional[NoteStatus] = Query(default=None, description="Filter by note processing status"),
    created_after: Optional[datetime] = Query(default=None, description="Filter notes created after this date"),
    created_before: Optional[datetime] = Query(default=None, description="Filter notes created before this date"),
    # Dependencies
    current_user: User = Depends(get_current_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get notes with pagination and filtering.

    Retrieves a paginated list of notes with optional filtering capabilities.
    Access is controlled by user role:

    - **AGENT users**: Can only see their own notes
    - **ADMIN users**: Can see all notes in the system

    ## Pagination
    - Use `page` and `size` parameters to control pagination
    - Maximum page size is 100 items
    - Response includes pagination metadata

    ## Filtering
    - **search**: Text search in note content and summary (case-insensitive)
    - **status**: Filter by processing status (queued, processing, done, failed)
    - **created_after**: Only notes created after this timestamp
    - **created_before**: Only notes created before this timestamp

    ## Response Format
    Returns a paginated response with:
    - `items`: Array of notes for the current page
    - `total`: Total number of matching notes
    - `page`: Current page number
    - `size`: Number of items per page
    - `pages`: Total number of pages

    ## Examples
    - `GET /notes?page=1&size=20` - First 20 notes
    - `GET /notes?search=meeting&status=done` - Search for completed meeting notes
    - `GET /notes?created_after=2025-01-01T00:00:00Z` - Notes from 2025 onwards
    """
    # Create pagination and filter objects
    pagination = PaginationParams(page=page, size=size)
    filters = NoteFilters(
        search=search,
        status=status,
        created_after=created_after,
        created_before=created_before
    )

    return await note_service.get_notes(current_user, pagination, filters)