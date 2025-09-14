"""
Filtering utilities for API endpoints.

This module provides standardized filtering functionality for database queries,
including text search, status filtering, and date range filtering.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query
from app.models import Note, NoteStatus


class NoteFilters(BaseModel):
    """
    Available filters for notes endpoints.

    Provides comprehensive filtering options for notes including text search,
    status filtering, and date range queries.

    Attributes:
        search: Text search in note content and summary
        status: Filter by note processing status
        created_after: Filter notes created after this date
        created_before: Filter notes created before this date
    """
    search: Optional[str] = Field(
        default=None,
        description="Search text in note content and summary",
        min_length=1,
        max_length=100
    )
    status: Optional[NoteStatus] = Field(
        default=None,
        description="Filter by note processing status"
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Filter notes created after this date (ISO format)"
    )
    created_before: Optional[datetime] = Field(
        default=None,
        description="Filter notes created before this date (ISO format)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search": "meeting",
                "status": "done",
                "created_after": "2025-01-01T00:00:00Z",
                "created_before": "2025-12-31T23:59:59Z"
            }
        }


def apply_note_filters(query: Query, filters: NoteFilters) -> Query:
    """
    Apply filtering conditions to a notes query.

    Args:
        query: Base SQLAlchemy query to filter
        filters: Filter parameters to apply

    Returns:
        Modified query with filter conditions applied

    Example:
        ```python
        base_query = select(Note)
        filters = NoteFilters(search="important", status=NoteStatus.done)
        filtered_query = apply_note_filters(base_query, filters)
        ```
    """
    conditions = []

    # Text search in raw_text and summary
    if filters.search:
        search_term = f"%{filters.search.lower()}%"
        search_condition = or_(
            Note.raw_text.ilike(search_term),
            Note.summary.ilike(search_term)
        )
        conditions.append(search_condition)

    # Status filtering
    if filters.status:
        conditions.append(Note.status == filters.status)

    # Date range filtering
    if filters.created_after:
        conditions.append(Note.created_at >= filters.created_after)

    if filters.created_before:
        conditions.append(Note.created_at <= filters.created_before)

    # Apply all conditions
    if conditions:
        query = query.where(and_(*conditions))

    return query