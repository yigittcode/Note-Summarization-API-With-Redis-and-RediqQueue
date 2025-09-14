from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import Note, NoteStatus, User, UserRole
from app.notes.schema import NoteCreate
from app.notes.interfaces import NoteRepositoryInterface
from app.common.pagination import PaginationParams, paginate_query
from app.common.filtering import NoteFilters, apply_note_filters
from typing import List, Optional, Tuple


class NoteRepository(NoteRepositoryInterface):
    """
    Repository class for Note database operations.

    Handles all database interactions for notes including CRUD operations,
    pagination, filtering, and role-based access control.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async SQLAlchemy database session
        """
        self.db = db

    async def create_note(self, note_create: NoteCreate, owner_id: int) -> Note:
        """
        Create a new note in the database.

        Args:
            note_create: Note creation data (raw_text)
            owner_id: ID of the user creating the note

        Returns:
            Created Note object with generated ID and timestamp

        Note:
            The note is created with status 'queued' and will be processed
            by a background worker for AI summarization.
        """
        note = Note(
            raw_text=note_create.raw_text,
            owner_id=owner_id,
            status=NoteStatus.queued
        )

        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_note_by_id(self, note_id: int, user: User) -> Optional[Note]:
        """
        Get a specific note by ID with role-based access control.

        Args:
            note_id: ID of the note to retrieve
            user: Current authenticated user

        Returns:
            Note object if found and accessible, None otherwise

        Note:
            AGENT users can only access their own notes.
            ADMIN users can access any note.
        """
        query = select(Note).where(Note.id == note_id)

        if user.role == UserRole.AGENT:
            query = query.where(Note.owner_id == user.id)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_notes(
        self,
        user: User,
        pagination: Optional[PaginationParams] = None,
        filters: Optional[NoteFilters] = None
    ) -> Tuple[List[Note], int]:
        """
        Get notes with optional pagination and filtering.

        Args:
            user: Current authenticated user
            pagination: Pagination parameters (page, size)
            filters: Filter criteria (search, status, date range)

        Returns:
            Tuple of (notes_list, total_count)

        Note:
            AGENT users can only see their own notes.
            ADMIN users can see all notes in the system.
        """
        # Base query with ordering (newest first)
        query = select(Note).order_by(desc(Note.created_at))

        # Apply role-based filtering
        if user.role == UserRole.AGENT:
            query = query.where(Note.owner_id == user.id)

        # Apply additional filters
        if filters:
            query = apply_note_filters(query, filters)

        # Apply pagination if provided
        if pagination:
            return await paginate_query(self.db, query, pagination)
        else:
            # Return all results without pagination
            result = await self.db.execute(query)
            notes = result.scalars().all()
            return notes, len(notes)

    async def update_note_status(self, note_id: int, status: NoteStatus, summary: Optional[str] = None, job_id: Optional[str] = None) -> Optional[Note]:
        result = await self.db.execute(select(Note).where(Note.id == note_id))
        note = result.scalars().first()

        if note:
            note.status = status
            if summary:
                note.summary = summary
            if job_id:
                note.job_id = job_id

            await self.db.commit()
            await self.db.refresh(note)

        return note