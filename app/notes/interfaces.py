from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from app.models import Note, NoteStatus, User
from app.notes.schema import NoteCreate
from app.common.pagination import PaginationParams
from app.common.filtering import NoteFilters


class NoteRepositoryInterface(ABC):
    """Abstract interface for note repository operations."""

    @abstractmethod
    async def create_note(self, note_create: NoteCreate, owner_id: int) -> Note:
        """Create a new note."""
        pass

    @abstractmethod
    async def get_note_by_id(self, note_id: int, user: User) -> Optional[Note]:
        """Get a note by ID with role-based access control."""
        pass

    @abstractmethod
    async def get_notes(
        self,
        user: User,
        pagination: Optional[PaginationParams] = None,
        filters: Optional[NoteFilters] = None
    ) -> Tuple[List[Note], int]:
        """Get notes with optional pagination and filtering."""
        pass

    @abstractmethod
    async def update_note_status(
        self,
        note_id: int,
        status: NoteStatus,
        summary: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Optional[Note]:
        """Update note status and optional fields."""
        pass