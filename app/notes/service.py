from app.notes.interfaces import NoteRepositoryInterface
from app.notes.schema import NoteCreate, NoteResponse
from app.models import User, NoteStatus
from app.common.exceptions import NoteNotFoundError, ServiceUnavailableError
from app.common.pagination import PaginationParams, PaginatedResponse, create_paginated_response
from app.common.filtering import NoteFilters
from typing import List, Optional
import logging
import redis
from rq import Queue
from app.core.config import settings

logger = logging.getLogger(__name__)


class NoteService:
    """
    Business logic service for note operations.

    Uses dependency injection to receive repository implementation,
    making the service testable and following SOLID principles.
    Handles note creation, retrieval, and coordination with background
    processing systems. Provides pagination and filtering capabilities.
    """

    def __init__(self, note_repository: NoteRepositoryInterface):
        """
        Initialize the service with injected repository.

        Args:
            note_repository: Repository implementation for note operations
        """
        self.repository = note_repository

    async def create_note(self, note_create: NoteCreate, user: User) -> NoteResponse:
        """
        Create a new note and queue it for AI summarization.

        Args:
            note_create: Note creation data
            user: User creating the note

        Returns:
            Created note with initial status 'queued'

        Note:
            This method automatically enqueues a background job for AI summarization.
            The note status will be updated to 'processing', then 'done' or 'failed'.
        """
        note = await self.repository.create_note(note_create, user.id)

        # Attempt to enqueue background summarization job
        try:
            redis_conn = redis.from_url(settings.redis_url)
            queue = Queue('summarization', connection=redis_conn)
            job = queue.enqueue('app.notes.tasks.summarize_note_task', note.id)
            await self.repository.update_note_status(note.id, note.status, job_id=job.id)
            logger.info(f"Successfully enqueued summarization job {job.id} for note {note.id}")
        except redis.ConnectionError as e:
            # Redis connection failure - return 503 Service Unavailable
            logger.error(f"Redis connection failed for note {note.id}: {e}", exc_info=True)
            try:
                await self.repository.update_note_status(note.id, NoteStatus.failed)
            except Exception:
                pass  # Don't fail the request if status update fails
            raise ServiceUnavailableError("Background processing service is currently unavailable")
        except Exception as e:
            # Other queue failures - log but don't fail the request
            logger.error(
                f"Failed to enqueue summary job for note {note.id}: {e}",
                exc_info=True
            )

            # Update note status to indicate queue failure
            try:
                await self.repository.update_note_status(note.id, NoteStatus.failed)
                logger.warning(f"Updated note {note.id} status to 'failed' due to queue failure")
            except Exception as status_update_error:
                logger.error(
                    f"Failed to update note {note.id} status after queue failure: {status_update_error}",
                    exc_info=True
                )

        return NoteResponse.model_validate(note)

    async def get_note(self, note_id: int, user: User) -> NoteResponse:
        note = await self.repository.get_note_by_id(note_id, user)
        if not note:
            raise NoteNotFoundError()

        return NoteResponse.model_validate(note)

    async def get_notes(
        self,
        user: User,
        pagination: Optional[PaginationParams] = None,
        filters: Optional[NoteFilters] = None
    ) -> PaginatedResponse[NoteResponse]:
        """
        Get notes with optional pagination and filtering.

        Args:
            user: Current authenticated user
            pagination: Pagination parameters (page, size)
            filters: Filter criteria (search, status, date range)

        Returns:
            Paginated response with notes and metadata

        Note:
            AGENT users can only see their own notes.
            ADMIN users can see all notes in the system.
        """
        notes, total = await self.repository.get_notes(user, pagination, filters)
        note_responses = [NoteResponse.model_validate(note) for note in notes]

        if pagination:
            return create_paginated_response(note_responses, total, pagination)
        else:
            # Return as paginated response with single page
            return PaginatedResponse[NoteResponse](
                items=note_responses,
                total=total,
                page=1,
                size=total,
                pages=1
            )