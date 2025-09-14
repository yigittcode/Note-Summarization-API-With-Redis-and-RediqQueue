"""
Tests demonstrating dependency injection benefits for testing.

These tests show how dependency injection makes unit testing easier
by allowing us to inject mock dependencies instead of real ones.
"""

import pytest
from app.users.service import UserService
from app.notes.service import NoteService
from app.users.schema import UserCreate, UserLogin
from app.notes.schema import NoteCreate
from app.models import UserRole, User, NoteStatus
from tests.mocks import MockUserRepository, MockNoteRepository
from app.common.exceptions import InvalidCredentialsError, UserAlreadyExistsError


class TestUserServiceWithDI:
    """Unit tests for UserService using dependency injection."""

    @pytest.mark.unit
    async def test_create_user_success(self):
        """Test successful user creation with mock repository."""
        # Arrange
        mock_repo = MockUserRepository()
        service = UserService(mock_repo)
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            role=UserRole.AGENT
        )

        # Act
        result = await service.create_user(user_data)

        # Assert
        assert result.email == "test@example.com"
        assert result.role == UserRole.AGENT
        assert "hashed_password" not in result.model_dump()

    @pytest.mark.unit
    async def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email."""
        # Arrange
        mock_repo = MockUserRepository()
        service = UserService(mock_repo)
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            role=UserRole.AGENT
        )

        # Create first user
        await service.create_user(user_data)

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(user_data)

    @pytest.mark.unit
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Arrange
        mock_repo = MockUserRepository()
        service = UserService(mock_repo)

        # Create user first
        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            role=UserRole.AGENT
        )
        await service.create_user(user_create)

        login_data = UserLogin(
            email="test@example.com",
            password="password123"
        )

        # Act
        result = await service.authenticate_user(login_data)

        # Assert
        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.unit
    async def test_authenticate_user_invalid_credentials(self):
        """Test authentication with wrong password."""
        # Arrange
        mock_repo = MockUserRepository()
        service = UserService(mock_repo)

        # Create user first
        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            role=UserRole.AGENT
        )
        await service.create_user(user_create)

        login_data = UserLogin(
            email="test@example.com",
            password="wrongpassword"
        )

        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(login_data)


class TestNoteServiceWithDI:
    """Unit tests for NoteService using dependency injection."""

    @pytest.mark.unit
    async def test_create_note_success(self):
        """Test successful note creation with mock repository."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)

        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Act
        result = await service.create_note(note_data, user)

        # Assert
        assert result.raw_text == "Test note content"
        assert result.status == NoteStatus.queued
        assert result.summary is None

    @pytest.mark.unit
    async def test_get_note_success(self):
        """Test retrieving note with mock repository."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)

        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Create note first
        created_note = await service.create_note(note_data, user)

        # Act
        result = await service.get_note(created_note.id, user)

        # Assert
        assert result.id == created_note.id
        assert result.raw_text == "Test note content"

    @pytest.mark.unit
    async def test_agent_cannot_access_other_notes(self):
        """Test that agents cannot access notes from other users."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)

        owner = User(id=1, email="owner@example.com", role=UserRole.AGENT)
        other_user = User(id=2, email="other@example.com", role=UserRole.AGENT)

        note_data = NoteCreate(raw_text="Private note")

        # Create note with first user
        created_note = await service.create_note(note_data, owner)

        # Act & Assert - second user tries to access note
        from app.common.exceptions import NoteNotFoundError
        with pytest.raises(NoteNotFoundError):
            await service.get_note(created_note.id, other_user)

    @pytest.mark.unit
    async def test_admin_can_access_all_notes(self):
        """Test that admins can access any note."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)

        agent = User(id=1, email="agent@example.com", role=UserRole.AGENT)
        admin = User(id=2, email="admin@example.com", role=UserRole.ADMIN)

        note_data = NoteCreate(raw_text="Agent's note")

        # Create note with agent
        created_note = await service.create_note(note_data, agent)

        # Act - admin accesses agent's note
        result = await service.get_note(created_note.id, admin)

        # Assert
        assert result.id == created_note.id
        assert result.raw_text == "Agent's note"

    @pytest.mark.unit
    async def test_get_notes_with_role_filtering(self):
        """Test that get_notes respects role-based access control."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)

        agent1 = User(id=1, email="agent1@example.com", role=UserRole.AGENT)
        agent2 = User(id=2, email="agent2@example.com", role=UserRole.AGENT)
        admin = User(id=3, email="admin@example.com", role=UserRole.ADMIN)

        # Create notes for both agents
        await service.create_note(NoteCreate(raw_text="Agent1 note 1"), agent1)
        await service.create_note(NoteCreate(raw_text="Agent1 note 2"), agent1)
        await service.create_note(NoteCreate(raw_text="Agent2 note 1"), agent2)

        # Act
        agent1_notes = await service.get_notes(agent1)
        agent2_notes = await service.get_notes(agent2)
        admin_notes = await service.get_notes(admin)

        # Assert
        assert agent1_notes.total == 2  # Agent1 sees only their notes
        assert agent2_notes.total == 1  # Agent2 sees only their note
        assert admin_notes.total == 3   # Admin sees all notes