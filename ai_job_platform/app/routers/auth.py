"""
Authentication Router — handles user registration, email/password login,
Google OAuth2 authentication, and current user session retrieval.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_google_id_token,
    verify_password,
)
from app.models.db_models import Profile, User
from app.schemas.auth_dto import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _build_user_response(user: User, db: AsyncSession) -> UserResponse:
    """Helper to find the user's latest active profile_id and construct UserResponse."""
    prof_res = await db.execute(
        select(Profile.id)
        .where(Profile.user_id == user.id)
        .order_by(Profile.created_at.desc())
        .limit(1)
    )
    latest_prof_id = prof_res.scalar_one_or_none()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        active_profile_id=str(latest_prof_id) if latest_prof_id else None,
    )


# ---------------------------------------------------------------------------
# 1. Register with Email & Password
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new user account with email and password."""
    norm_email = body.email.strip().lower()

    # Check if email is already taken
    existing = await db.execute(select(User).where(User.email == norm_email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please log in.",
        )

    # Hash password securely
    hashed_pw = hash_password(body.password)

    new_user = User(
        email=norm_email,
        full_name=body.full_name.strip() if body.full_name else None,
        hashed_password=hashed_pw,
        auth_provider="email",
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
    user_resp = await _build_user_response(new_user, db)

    return AuthResponse(access_token=token, token_type="bearer", user=user_resp)


# ---------------------------------------------------------------------------
# 2. Login with Email & Password
# ---------------------------------------------------------------------------

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates a user using email and password."""
    norm_email = body.email.strip().lower()

    result = await db.execute(select(User).where(User.email == norm_email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # If user registered via Google only without a password
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was created with Google Sign-In. Please click 'Continue with Google'.",
        )

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    user_resp = await _build_user_response(user, db)

    return AuthResponse(access_token=token, token_type="bearer", user=user_resp)


# ---------------------------------------------------------------------------
# 3. Google OAuth2 Sign-In / Sign-Up
# ---------------------------------------------------------------------------

@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticates or auto-registers a user via a Google ID token from Google Identity Services.
    """
    google_data = verify_google_id_token(body.credential)
    if not google_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired Google authentication credential.",
        )

    google_email = google_data["email"].strip().lower()
    google_sub = google_data["google_sub"]

    # Check if user exists by email or google_sub
    result = await db.execute(
        select(User).where((User.email == google_email) | (User.google_sub == google_sub))
    )
    user = result.scalar_one_or_none()

    if user:
        # Existing user: link google_sub and avatar if missing
        if not user.google_sub:
            user.google_sub = google_sub
        if google_data.get("avatar_url") and not user.avatar_url:
            user.avatar_url = google_data["avatar_url"]
        if not user.full_name and google_data.get("full_name"):
            user.full_name = google_data["full_name"]
        await db.commit()
    else:
        # New user: auto-create account
        user = User(
            email=google_email,
            full_name=google_data.get("full_name") or None,
            hashed_password=None,
            auth_provider="google",
            google_sub=google_sub,
            avatar_url=google_data.get("avatar_url") or None,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    user_resp = await _build_user_response(user, db)

    return AuthResponse(access_token=token, token_type="bearer", user=user_resp)


# ---------------------------------------------------------------------------
# 4. Get Current User Session & Active Profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns profile information and the latest active profile_id for the logged-in user.
    """
    return await _build_user_response(current_user, db)
