"""
Profiles Router — handles profile retrieval, manual edits and profile management.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import Profile, User
from app.schemas.dto import APIResponse, ProfileUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

SEED_USER_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174004")


@router.get("/me", response_model=APIResponse)
async def get_my_active_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the current logged-in user's latest saved profile facts.
    """
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == current_user.id)
        .order_by(Profile.created_at.desc())
        .limit(1)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found for your account. Please upload a resume first.",
        )

    return APIResponse(
        success=True,
        message="Active profile retrieved.",
        data={
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "source_filename": profile.source_filename,
            "parsed_json": profile.parsed_json,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
        },
    )


@router.post("/{profile_id}/claim", response_model=APIResponse)
async def claim_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Links a guest-uploaded profile to the currently logged-in user.
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    # Re-assign to current user if unowned or owned by default seed user
    if profile.user_id == SEED_USER_ID or profile.user_id == current_user.id:
        profile.user_id = current_user.id
        await db.commit()
        return APIResponse(
            success=True,
            message="Profile claimed and linked to your account successfully.",
            data={"profile_id": str(profile.id), "user_id": str(current_user.id)},
        )

    # If it already belongs to another user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This profile belongs to a different user account.",
    )


@router.get("/{profile_id}", response_model=APIResponse)
async def get_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve profile details by profile ID for the frontend profile editor.
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    return APIResponse(
        success=True,
        message="Profile retrieved successfully.",
        data={
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "source_filename": profile.source_filename,
            "parsed_json": profile.parsed_json,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
        }
    )


@router.patch("/{profile_id}", response_model=APIResponse)
async def update_profile(
    profile_id: uuid.UUID,
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually update specific fields in a parsed profile's JSON data.
    Allows users to correct AI parsing mistakes to improve match accuracy.
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        
    current_data = profile.parsed_json or {}

    # If full JSON object was provided directly from ProfilePage.jsx editor
    if body.parsed_json is not None:
        current_data = body.parsed_json
    else:
        # 1. Handle nested summary update (lives inside personal_info)
        if body.summary is not None:
            if "personal_info" not in current_data:
                current_data["personal_info"] = {}
            current_data["personal_info"]["summary"] = body.summary

        # 2. Handle root-level list updates
        if body.skills is not None:
            current_data["skills"] = body.skills
            
        if body.experience is not None:
            current_data["experience"] = [item.model_dump(exclude_unset=True) for item in body.experience]
            
        if body.projects is not None:
            current_data["projects"] = [item.model_dump(exclude_unset=True) for item in body.projects]
            
        if body.education is not None:
            current_data["education"] = [item.model_dump(exclude_unset=True) for item in body.education]

    # 3. Explicitly flag the JSON column as modified so SQLAlchemy knows to save it.
    profile.parsed_json = current_data
    flag_modified(profile, "parsed_json")
    
    await db.flush()

    return APIResponse(
        success=True,
        message="Profile updated successfully.",
        data={
            "id": str(profile.id),
            "parsed_json": current_data
        }
    )
