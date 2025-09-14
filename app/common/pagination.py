"""
Pagination utilities for API endpoints.

This module provides standardized pagination functionality across the application,
including query parameter parsing, database query modification, and response formatting.
"""

from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Standard pagination query parameters.

    Attributes:
        page: Page number (1-based indexing)
        size: Number of items per page (max 100)
    """
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value for the current page."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response format.

    Generic response wrapper that provides consistent pagination metadata
    across all paginated endpoints in the API.

    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        size: Number of items per page
        pages: Total number of pages
    """
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 2,
                "size": 10,
                "pages": 15
            }
        }


async def paginate_query(
    session: AsyncSession,
    query,
    pagination: PaginationParams
) -> tuple[List, int]:
    """
    Apply pagination to a SQLAlchemy query and execute it.

    Args:
        session: Async database session
        query: SQLAlchemy select query to paginate
        pagination: Pagination parameters

    Returns:
        Tuple of (items, total_count) where items is the paginated results
        and total_count is the total number of items without pagination
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    paginated_query = query.offset(pagination.offset).limit(pagination.size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return items, total


def create_paginated_response(
    items: List[T],
    total: int,
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response.

    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        pagination: Pagination parameters used

    Returns:
        PaginatedResponse with all metadata calculated
    """
    pages = (total + pagination.size - 1) // pagination.size  # Ceiling division

    return PaginatedResponse[T](
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pages
    )