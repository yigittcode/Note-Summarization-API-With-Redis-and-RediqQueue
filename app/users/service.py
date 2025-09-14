from datetime import timedelta
from app.users.interfaces import UserRepositoryInterface
from app.users.schema import UserCreate, UserLogin, UserResponse, Token
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.common.exceptions import InvalidCredentialsError
from typing import Optional


class UserService:
    """
    Business logic service for user operations.

    Uses dependency injection to receive repository implementation,
    making the service testable and following SOLID principles.
    """

    def __init__(self, user_repository: UserRepositoryInterface):
        """
        Initialize the service with injected repository.

        Args:
            user_repository: Repository implementation for user operations
        """
        self.repository = user_repository

    async def create_user(self, user_create: UserCreate) -> UserResponse:
        user = await self.repository.create_user(user_create)
        return UserResponse.model_validate(user)

    async def authenticate_user(self, user_login: UserLogin) -> Token:
        user = await self.repository.get_user_by_email(user_login.email)
        if not user or not verify_password(user_login.password, user.hashed_password):
            raise InvalidCredentialsError()

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")