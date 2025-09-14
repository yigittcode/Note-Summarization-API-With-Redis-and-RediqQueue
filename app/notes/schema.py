"""
Pydantic schemas for note-related API requests and responses.

This module defines the data structures used for validating and serializing
note data in API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models import NoteStatus


class NoteCreate(BaseModel):
    """
    Schema for creating a new note.

    Used in POST /notes/ endpoint to validate the request body.
    """
    raw_text: str = Field(
        ...,
        description="The text content to be summarized",
        min_length=1,
        max_length=10000,
        example="Important meeting notes about quarterly review and project updates"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "raw_text": "Important meeting notes about quarterly review and urgent decisions for Q4 planning"
            }
        }


class NoteResponse(BaseModel):
    """
    Schema for note response data.

    Used in all note-related API responses to ensure consistent data format.
    Includes all note fields except sensitive internal data.
    """
    id: int = Field(..., description="Unique note identifier")
    raw_text: str = Field(..., description="Original note content")
    summary: Optional[str] = Field(None, description="AI-generated summary (available when status is 'done')")
    status: NoteStatus = Field(..., description="Processing status of the note")
    created_at: datetime = Field(..., description="Timestamp when the note was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the note was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "raw_text": "Important meeting notes about quarterly review",
                "summary": "Priority summary: Important meeting notes about quarterly review...",
                "status": "done",
                "created_at": "2025-09-14T10:00:00Z",
                "updated_at": "2025-09-14T10:00:05Z"
            }
        }