"""
Dependency injection providers for FastAPI.

This module provides FastAPI dependency functions that create service instances
with proper dependency injection. This approach makes testing easier and
follows SOLID principles.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.users.service import UserService
from app.users.repository import UserRepository
from app.users.interfaces import UserRepositoryInterface
from app.notes.service import NoteService
from app.notes.repository import NoteRepository
from app.notes.interfaces import NoteRepositoryInterface


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepositoryInterface:
    """
    Dependency provider for user repository.

    Args:
        db: Database session dependency

    Returns:
        UserRepositoryInterface implementation
    """
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepositoryInterface = Depends(get_user_repository)
) -> UserService:
    """
    Dependency provider for user service with injected repository.

    Args:
        user_repository: Injected user repository

    Returns:
        UserService instance with dependencies injected
    """
    return UserService(user_repository)


def get_note_repository(db: AsyncSession = Depends(get_db)) -> NoteRepositoryInterface:
    """
    Dependency provider for note repository.

    Args:
        db: Database session dependency

    Returns:
        NoteRepositoryInterface implementation
    """
    return NoteRepository(db)


def get_note_service(
    note_repository: NoteRepositoryInterface = Depends(get_note_repository)
) -> NoteService:
    """
    Dependency provider for note service with injected repository.

    Args:
        note_repository: Injected note repository

    Returns:
        NoteService instance with dependencies injected
    """
    return NoteService(note_repository)