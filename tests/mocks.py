"""
Mock implementations for testing with dependency injection.

These mocks demonstrate how dependency injection makes testing easier
by allowing us to replace real implementations with test doubles.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.users.interfaces import UserRepositoryInterface
from app.notes.interfaces import NoteRepositoryInterface
from app.models import User, Note, UserRole, NoteStatus
from app.users.schema import UserCreate
from app.notes.schema import NoteCreate
from app.common.pagination import PaginationParams
from app.common.filtering import NoteFilters
from app.core.security import get_password_hash


class MockUserRepository(UserRepositoryInterface):
    """Mock user repository for testing."""

    def __init__(self):
        self.users: Dict[int, User] = {}
        self.next_id = 1

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from memory store."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID from memory store."""
        return self.users.get(user_id)

    async def create_user(self, user_create: UserCreate) -> User:
        """Create user in memory store."""
        # Check for duplicate email
        existing = await self.get_user_by_email(user_create.email)
        if existing:
            from app.common.exceptions import UserAlreadyExistsError
            raise UserAlreadyExistsError()

        user = User(
            id=self.next_id,
            email=user_create.email,
            hashed_password=get_password_hash(user_create.password),
            role=user_create.role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users[self.next_id] = user
        self.next_id += 1
        return user


class MockNoteRepository(NoteRepositoryInterface):
    """Mock note repository for testing."""

    def __init__(self):
        self.notes: Dict[int, Note] = {}
        self.next_id = 1

    async def create_note(self, note_create: NoteCreate, owner_id: int) -> Note:
        """Create note in memory store."""
        note = Note(
            id=self.next_id,
            raw_text=note_create.raw_text,
            owner_id=owner_id,
            status=NoteStatus.queued,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.notes[self.next_id] = note
        self.next_id += 1
        return note

    async def get_note_by_id(self, note_id: int, user: User) -> Optional[Note]:
        """Get note by ID with role-based access control."""
        note = self.notes.get(note_id)
        if not note:
            return None

        # Apply role-based access control
        if user.role == UserRole.AGENT and note.owner_id != user.id:
            return None

        return note

    async def get_notes(
        self,
        user: User,
        pagination: Optional[PaginationParams] = None,
        filters: Optional[NoteFilters] = None
    ) -> Tuple[List[Note], int]:
        """Get notes with filtering and pagination."""
        # Start with all notes
        notes = list(self.notes.values())

        # Apply role-based filtering
        if user.role == UserRole.AGENT:
            notes = [note for note in notes if note.owner_id == user.id]

        # Apply filters
        if filters:
            if filters.search:
                search_lower = filters.search.lower()
                notes = [
                    note for note in notes
                    if search_lower in note.raw_text.lower() or
                    (note.summary and search_lower in note.summary.lower())
                ]
            if filters.status:
                notes = [note for note in notes if note.status == filters.status]

        total = len(notes)

        # Apply pagination
        if pagination:
            start = (pagination.page - 1) * pagination.size
            end = start + pagination.size
            notes = notes[start:end]

        return notes, total

    async def update_note_status(
        self,
        note_id: int,
        status: NoteStatus,
        summary: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Optional[Note]:
        """Update note status and optional fields."""
        note = self.notes.get(note_id)
        if note:
            note.status = status
            if summary:
                note.summary = summary
            if job_id:
                note.job_id = job_id
        return note