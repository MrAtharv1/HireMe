"""
Authentication and User Account DTOs.
"""

from __future__ import annotations

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters.")
    full_name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token JWT received from Google Identity Services.")


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    auth_provider: str = "email"
    avatar_url: Optional[str] = None
    is_active: bool = True
    active_profile_id: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
