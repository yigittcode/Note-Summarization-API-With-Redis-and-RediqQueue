from abc import ABC, abstractmethod
from typing import Optional
from app.models import User
from app.users.schema import UserCreate


class UserRepositoryInterface(ABC):
    """Abstract interface for user repository operations."""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        pass