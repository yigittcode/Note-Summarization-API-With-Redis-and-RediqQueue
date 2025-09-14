"""
Pydantic schemas for user authentication and management.

This module defines the data structures used for user registration,
authentication, and API responses related to user operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models import UserRole


class UserCreate(BaseModel):
    """
    Schema for user registration.

    Used in POST /users/signup endpoint to validate new user data.
    """
    email: EmailStr = Field(..., description="Valid email address (must be unique)")
    password: str = Field(
        ...,
        description="User password",
        min_length=8,
        max_length=100,
        example="securepassword123"
    )
    role: UserRole = Field(
        default=UserRole.AGENT,
        description="User role - AGENT (default) or ADMIN"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "role": "AGENT"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user authentication.

    Used in POST /users/login endpoint to validate login credentials.
    """
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Used in signup and profile endpoints. Excludes sensitive data like passwords.
    """
    id: int = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")
    role: UserRole = Field(..., description="User's role (AGENT or ADMIN)")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "AGENT",
                "created_at": "2025-09-14T10:00:00Z"
            }
        }


class Token(BaseModel):
    """
    Schema for JWT authentication token response.

    Used in POST /users/login endpoint response to provide access token.
    """
    access_token: str = Field(..., description="JWT access token for API authentication")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }