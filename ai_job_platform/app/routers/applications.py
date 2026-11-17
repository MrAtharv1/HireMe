"""
Applications Router — handles job application tracking.
"""

from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db_models import Application, Job, Profile
from app.schemas.dto import ApplicationCreate, ApplicationResponse, ApplicationUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(body: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    """Records a new job application and returns the external apply URL."""
    # 1. Validate Job exists
    job = (await db.execute(select(Job).where(Job.id == body.job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # 2. Validate Profile exists
    profile = (await db.execute(select(Profile).where(Profile.id == body.profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # 3. Check for duplicate application
    existing = await db.execute(
        select(Application).where(Application.job_id == body.job_id, Application.profile_id == body.profile_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already applied to this job.")

    # 4. Create Application
    application = Application(
        profile_id=body.profile_id,
        job_id=body.job_id,
        resume_version_id=body.resume_version_id,
        notes=body.notes,
    )
    db.add(application)
    await db.flush()

    # 5. Hydrate response with Job details for frontend convenience
    response_data = ApplicationResponse.model_validate(application)
    response_data.apply_url = job.apply_url
    response_data.job_title = job.title
    response_data.company = job.company

    return response_data


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID, body: ApplicationUpdate, db: AsyncSession = Depends(get_db)
):
    """Updates the status or notes of an existing application."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if body.status is not None:
        application.status = body.status
    if body.notes is not None:
        application.notes = body.notes

    await db.flush()
    
    # Hydrate response
    response_data = ApplicationResponse.model_validate(application)
    response_data.apply_url = application.job.apply_url
    response_data.job_title = application.job.title
    response_data.company = application.job.company
    
    return response_data


@router.get("/{profile_id}", response_model=List[ApplicationResponse])
async def list_applications(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Lists all job applications for a specific profile."""
    # Verify profile exists
    profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Fetch applications (job relation is eager loaded via selectin mapping in db_models)
    result = await db.execute(
        select(Application)
        .where(Application.profile_id == profile_id)
        .order_by(Application.applied_at.desc())
    )
    applications = result.scalars().all()

    # Hydrate responses
    responses = []
    for app in applications:
        dto = ApplicationResponse.model_validate(app)
        dto.apply_url = app.job.apply_url
        dto.job_title = app.job.title
        dto.company = app.job.company
        responses.append(dto)

    return responses