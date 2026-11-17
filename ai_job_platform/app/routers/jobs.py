"""
Jobs Router — handles job ingestion, recommendations, job details, and specific job tailoring.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db_models import Job, Profile
from app.schemas.dto import JobDetailResponse, JobTailorResponse
from app.services.job_fetcher import fetch_and_store_jobs
from app.services.matcher import calculate_match_score
from app.services.resume_service import tailor_and_generate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobRecommendation(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    apply_url: str
    score: int
    reasons: List[str]


class RecommendedJobCard(BaseModel):
    id: str
    title: str
    company: str
    location: str
    apply_url: str
    source: str
    posted_at: Optional[datetime] = None
    fresher_score: int
    match_percent: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    reason: str


@router.get("/recommended", response_model=List[RecommendedJobCard], summary="Get filtered fresher job recommendations")
async def get_recommended_jobs(
    profile_id: Optional[uuid.UUID] = Query(None, description="Candidate Profile UUID"),
    min_fresher_score: int = Query(60, description="Minimum fresher score threshold (0-100)"),
    min_match: int = Query(0, description="Minimum match percentage"),
    role: Optional[str] = Query(None, description="Filter by title / role keyword"),
    location: Optional[str] = Query(None, description="Filter by location"),
    remote_only: bool = Query(False, description="Filter for remote jobs only"),
    max_days_old: Optional[int] = Query(None, description="Only jobs posted within N days"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns high-confidence fresher-appropriate jobs filtered through the 3-stage funnel.
    Sorted by (fresher_score * match_percent) descending.
    """
    from datetime import datetime, timezone
    from app.services.job_classifier import check_stage1_rules, compute_fresher_score

    # 1. Fetch Profile if provided
    candidate_skills: List[str] = []
    if profile_id:
        profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
        if profile and profile.parsed_json:
            candidate_skills = profile.parsed_json.get("skills", [])

    # 2. Query active jobs
    query = select(Job).where(Job.is_active == True)
    if remote_only:
        query = query.where(Job.remote == True)
    
    result = await db.execute(query)
    jobs = result.scalars().all()

    now = datetime.now(timezone.utc)
    cards: List[RecommendedJobCard] = []

    for job in jobs:
        # Check days old filter if requested
        if max_days_old and job.posted_at:
            p_at = job.posted_at.replace(tzinfo=timezone.utc) if job.posted_at.tzinfo is None else job.posted_at
            if (now - p_at).total_seconds() / 86400.0 > max_days_old:
                continue

        # Location filter
        if location and location.lower() not in (job.location or "").lower():
            continue

        # Role filter
        if role and role.lower() not in job.title.lower():
            continue

        # Stage 1 Rule Check
        stage1 = check_stage1_rules(job.title, job.description)
        if not stage1["passed"]:
            continue

        # Stage 3 Scoring
        fresher_score, match_pct, matched, missing, fit_reason = compute_fresher_score(
            seniority=job.seniority_level or ("intern" if stage1["is_obvious_fresher"] else "entry"),
            min_years=job.min_years_exp if job.min_years_exp is not None else stage1["min_years"],
            title=job.title,
            description=job.description,
            posted_at=job.posted_at,
            candidate_skills=candidate_skills,
            required_skills=job.skills_required if isinstance(job.skills_required, list) else None,
        )

        if fresher_score < min_fresher_score:
            continue
        if match_pct < min_match:
            continue

        cards.append(RecommendedJobCard(
            id=str(job.id),
            title=job.title,
            company=job.company,
            location=job.location or "Remote",
            apply_url=job.apply_url or "",
            source=job.source or "web",
            posted_at=job.posted_at,
            fresher_score=fresher_score,
            match_percent=match_pct,
            matched_skills=matched,
            missing_skills=missing,
            reason=fit_reason,
        ))

    # Sort descending by composite ranking: fresher_score * match_percent
    cards.sort(key=lambda c: c.fresher_score * c.match_percent, reverse=True)
    return cards[:limit]


@router.post("/ingest", summary="Fetch jobs from Remotive API")
async def ingest_jobs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Pulls remote jobs into the database across multiple categories."""
    return await fetch_and_store_jobs(db, limit)


@router.get(
    "/{job_id}", 
    response_model=JobDetailResponse, 
    summary="Get job details with optional match insights"
)
async def get_job_detail(
    job_id: uuid.UUID,
    profile_id: Optional[uuid.UUID] = Query(None, description="Provide a profile_id to get personalized match insights"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details for a specific job listing.
    If `profile_id` is provided, dynamically calculates and returns the match score and reasoning.
    """
    # 1. Fetch Job
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    score = None
    reasons = None

    # 2. Calculate match if profile_id is provided
    if profile_id:
        profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        score, reasons = calculate_match_score(profile.parsed_json, job)

    return JobDetailResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        apply_url=job.apply_url,
        created_at=job.created_at,
        match_score=score,
        match_reasons=reasons
    )


@router.get("/recommendations/{profile_id}", response_model=List[JobRecommendation])
async def get_recommendations(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns a diversified mix of 25 job recommendations:
    - 40% High-score (Stretch)
    - 40% Mid-score (Realistic)
    - 20% Low-score but easy-entry (Callback focused)
    """
    # 1. Get Profile
    profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        
    profile_json = profile.parsed_json

    # 2. Get active jobs
    jobs_result = await db.execute(select(Job).where(Job.is_active == True))
    all_jobs = jobs_result.scalars().all()
    
    if not all_jobs:
        # Auto-ingest jobs if table is empty
        try:
            logger.info("No jobs found in database. Auto-ingesting from Remotive API...")
            await fetch_and_store_jobs(db, limit=20)
            jobs_result = await db.execute(select(Job).where(Job.is_active == True))
            all_jobs = jobs_result.scalars().all()
        except Exception as ingest_err:
            logger.warning("Auto-ingestion failed: %s", ingest_err)

    if not all_jobs:
        return []

    # 3. Score and tag jobs
    scored_jobs = []
    easy_keywords = ["qa", "support", "analyst", "trainee", "quality assurance", "entry", "junior"]
    easy_categories = ["qa", "customer-support", "data"]

    for job in all_jobs:
        score, reasons = calculate_match_score(profile_json, job)
        
        is_easy_entry = getattr(job, "category", "") in easy_categories or \
                        any(kw in job.title.lower() for kw in easy_keywords)
        
        if score > 0 or is_easy_entry:  
            scored_jobs.append({
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company or "Unknown",
                "location": job.location or "Remote",
                "apply_url": job.apply_url or "",
                "score": score,
                "reasons": reasons,
                "_is_easy": is_easy_entry # Temporary tracking flag
            })
            
    # 4. Bucketing logic
    high_bucket = [j for j in scored_jobs if j["score"] >= 70]
    mid_bucket = [j for j in scored_jobs if 40 <= j["score"] < 70]
    easy_bucket = [j for j in scored_jobs if j["score"] < 40 and j["_is_easy"]]
    
    # Sort each bucket descending by score
    high_bucket.sort(key=lambda x: x["score"], reverse=True)
    mid_bucket.sort(key=lambda x: x["score"], reverse=True)
    easy_bucket.sort(key=lambda x: x["score"], reverse=True)
    
    # Enforce 40/40/20 mix (10 / 10 / 5)
    final_mix = []
    final_mix.extend(high_bucket[:10])
    final_mix.extend(mid_bucket[:10])
    final_mix.extend(easy_bucket[:5])
    
    # 5. Graceful backfill (if a bucket was short, pull from remaining jobs)
    if len(final_mix) < 25:
        used_ids = {j["job_id"] for j in final_mix}
        remaining = sorted(
            [j for j in scored_jobs if j["job_id"] not in used_ids],
            key=lambda x: x["score"],
            reverse=True
        )
        needed = 25 - len(final_mix)
        final_mix.extend(remaining[:needed])
        
    # Clean up internal flags and sort the final payload by score
    final_mix.sort(key=lambda x: x["score"], reverse=True)
    for item in final_mix:
        item.pop("_is_easy", None)
        
    return final_mix


@router.post("/{job_id}/tailor/{profile_id}", response_model=JobTailorResponse, summary="Tailor a profile to a specific job")
async def tailor_for_job(
    job_id: uuid.UUID, 
    profile_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a tailored resume and PDF specifically targeted at a specific job listing.
    """
    # 1. Fetch Profile and Job
    profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    # 2. Execute Tailoring & PDF Generation
    try:
        version, summary = await tailor_and_generate(
            profile_json=profile.parsed_json,
            job_description=job.description,
            user_id=profile.user_id,
            job_id=job.id,
            db=db
        )
    except Exception as exc:
        logger.exception("Job tailoring failed for Job %s and Profile %s", job_id, profile_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to tailor resume: {str(exc)}"
        )

    # 3. Return formatted response
    return JobTailorResponse(
        resume_version_id=version.id,
        download_url=f"/api/v1/resume/download/{version.id}",
        changes_summary=summary
    )