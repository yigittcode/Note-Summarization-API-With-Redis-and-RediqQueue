"""
SQLAlchemy database models for the Testcase Codex application.

This module defines the database schema including users, notes, and their relationships.
All models use async-compatible SQLAlchemy 2.0+ syntax.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(enum.Enum):
    """
    Enumeration of available user roles.

    - ADMIN: Can access all notes in the system
    - AGENT: Can only access their own notes
    """
    ADMIN = "ADMIN"
    AGENT = "AGENT"


class NoteStatus(enum.Enum):
    """
    Enumeration of note processing statuses.

    - queued: Note is waiting for AI processing
    - processing: Note is currently being processed by AI
    - done: AI processing completed successfully
    - failed: AI processing failed
    """
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class User(Base):
    """
    User model for authentication and authorization.

    Stores user credentials and role information. Users can be either
    ADMIN (access all notes) or AGENT (access only their own notes).

    Attributes:
        id: Primary key
        email: Unique email address for login
        hashed_password: Bcrypt-hashed password
        role: User role (ADMIN or AGENT)
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
        notes: Relationship to user's notes
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole, name="userrole"), nullable=False, default=UserRole.AGENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    notes = relationship("Note", back_populates="owner")


class Note(Base):
    """
    Note model for storing user content and AI summaries.

    Stores user-submitted text content along with AI-generated summaries
    and processing status. Each note belongs to a specific user.

    Attributes:
        id: Primary key
        raw_text: Original user-submitted text content
        summary: AI-generated summary (populated after processing)
        status: Processing status (queued, processing, done, failed)
        job_id: Background job ID for tracking async processing
        owner_id: Foreign key to the user who created the note
        created_at: Note creation timestamp
        updated_at: Last modification timestamp
        owner: Relationship to the note's owner (User)
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text)
    status = Column(SQLEnum(NoteStatus, name="notestatus"), nullable=False, default=NoteStatus.queued)
    job_id = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="notes")