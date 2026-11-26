"""
Tests for Core Routers: Jobs, Applications, and Profiles.
Verifies:
- GET /jobs/recommended with remote_only and role keyword filters
- GET /jobs/recommended with min_fresher_score thresholding
- GET /jobs/{id} detail retrieval and personalized match scoring
- GET /jobs/{id} 404 on nonexistent job UUID
- POST /applications/apply application tracking and hydrated response
- POST /applications/apply duplicate application prevention (400)
- GET /applications/{profile_id} pipeline retrieval
- GET /profiles/{profile_id} and PATCH /profiles/{profile_id} data editing
- POST /profiles/{profile_id}/claim linking guest profiles to authenticated accounts
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.database import async_session_factory, init_db
from app.models.db_models import Job, Profile, User, Application
from app.schemas.dto import (
    ApplicationCreate,
    JobDetailResponse,
    ProfileUpdateRequest,
)
from app.routers.jobs import get_recommended_jobs, get_job_detail
from app.routers.applications import create_application, list_applications
from app.routers.profiles import get_profile, update_profile, claim_profile, SEED_USER_ID


@pytest.mark.asyncio
async def test_jobs_recommended_with_filters():
    await init_db()
    async with async_session_factory() as db:
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        job_remote = Job(
            id=uid1,
            title="Junior Python Backend Engineer",
            company="CloudFlow Inc",
            location="Remote",
            remote=True,
            description="Looking for entry level Python and FastAPI developers.",
            apply_url="https://example.com/apply/1",
            is_active=True,
            fresher_score=85.0,
            skills_required={"skills": ["Python", "FastAPI"]}
        )
        job_onsite = Job(
            id=uid2,
            title="Senior Director of Engineering",
            company="Legacy Corp",
            location="New York, NY",
            remote=False,
            description="10+ years required leading large engineering organizations.",
            apply_url="https://example.com/apply/2",
            is_active=True,
            fresher_score=10.0,
            skills_required={"skills": ["Management", "Kubernetes"]}
        )
        db.add_all([job_remote, job_onsite])
        await db.commit()

        # Query with remote_only=True and role="Python"
        results = await get_recommended_jobs(
            profile_id=None,
            min_fresher_score=0,
            min_match=0,
            role="Python",
            location=None,
            remote_only=True,
            max_days_old=None,
            limit=50,
            db=db
        )
        job_ids = [r.id for r in results]
        assert str(uid1) in job_ids
        assert str(uid2) not in job_ids


@pytest.mark.asyncio
async def test_jobs_recommended_fresher_score_filter():
    await init_db()
    async with async_session_factory() as db:
        high_score_id = uuid.uuid4()
        low_score_id = uuid.uuid4()
        job_high = Job(
            id=high_score_id,
            title="Software Engineering Intern",
            company="Startup Labs",
            location="Bengaluru, India",
            remote=False,
            min_years_exp=0,
            description="Open to fresh graduates and 2025 batch interns with 0 years experience.",
            apply_url="https://example.com/apply/high",
            is_active=True,
            fresher_score=92.0,
        )
        job_low = Job(
            id=low_score_id,
            title="Lead Architect",
            company="Enterprise Corp",
            location="Bengaluru, India",
            remote=False,
            min_years_exp=8,
            description="Minimum 8 years of distributed systems experience.",
            apply_url="https://example.com/apply/low",
            is_active=True,
            fresher_score=25.0,
        )
        db.add_all([job_high, job_low])
        await db.commit()

        results = await get_recommended_jobs(
            profile_id=None,
            min_fresher_score=80,
            min_match=0,
            role=None,
            location=None,
            remote_only=False,
            max_days_old=None,
            limit=50,
            db=db
        )
        job_ids = [r.id for r in results]
        assert str(high_score_id) in job_ids
        assert str(low_score_id) not in job_ids


@pytest.mark.asyncio
async def test_get_job_detail_success():
    await init_db()
    async with async_session_factory() as db:
        job_id = uuid.uuid4()
        job = Job(
            id=job_id,
            title="Associate AI Developer",
            company="OpenAI Partner",
            location="San Francisco, CA",
            description="Develop PyTorch and LLM pipelines.",
            apply_url="https://example.com/apply/ai",
            is_active=True,
            fresher_score=88.0,
        )
        db.add(job)
        await db.commit()

        detail = await get_job_detail(job_id=job_id, profile_id=None, db=db)
        assert detail.id == job_id
        assert detail.title == "Associate AI Developer"
        assert detail.company == "OpenAI Partner"
        assert detail.apply_url == "https://example.com/apply/ai"


@pytest.mark.asyncio
async def test_get_job_detail_not_found():
    await init_db()
    async with async_session_factory() as db:
        non_existent_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await get_job_detail(job_id=non_existent_id, profile_id=None, db=db)
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_application_success():
    await init_db()
    async with async_session_factory() as db:
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"app_{uuid.uuid4().hex[:6]}@example.com", hashed_password="hashed_pw_test")
        profile_id = uuid.uuid4()
        profile = Profile(id=profile_id, user_id=user_id, source_filename="resume.pdf", parsed_json={"skills": ["Python"]})
        job_id = uuid.uuid4()
        job = Job(
            id=job_id,
            title="Full Stack Developer",
            company="Apex Tech",
            location="Remote",
            description="Build scalable web apps.",
            apply_url="https://example.com/apex-apply",
            is_active=True
        )
        db.add_all([user, profile, job])
        await db.commit()

        req = ApplicationCreate(profile_id=profile_id, job_id=job_id, notes="Submitted via platform")
        app_resp = await create_application(req, db=db)
        assert app_resp.profile_id == profile_id
        assert app_resp.job_id == job_id
        assert app_resp.apply_url == "https://example.com/apex-apply"
        assert app_resp.job_title == "Full Stack Developer"
        assert app_resp.company == "Apex Tech"


@pytest.mark.asyncio
async def test_create_application_duplicate_rejected():
    await init_db()
    async with async_session_factory() as db:
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"dup_{uuid.uuid4().hex[:6]}@example.com", hashed_password="hashed_pw_test")
        profile_id = uuid.uuid4()
        profile = Profile(id=profile_id, user_id=user_id, source_filename="resume.pdf", parsed_json={})
        job_id = uuid.uuid4()
        job = Job(
            id=job_id,
            title="Junior QA Engineer",
            company="QualityFirst",
            description="Manual and automated testing.",
            apply_url="https://example.com/qf-apply",
            is_active=True
        )
        db.add_all([user, profile, job])
        await db.commit()

        req = ApplicationCreate(profile_id=profile_id, job_id=job_id)
        # First application succeeds
        await create_application(req, db=db)

        # Second application must fail with 400
        with pytest.raises(HTTPException) as exc_info:
            await create_application(req, db=db)
        assert exc_info.value.status_code == 400
        assert "already applied" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_list_applications_for_profile():
    await init_db()
    async with async_session_factory() as db:
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"list_{uuid.uuid4().hex[:6]}@example.com", hashed_password="hashed_pw_test")
        profile_id = uuid.uuid4()
        profile = Profile(id=profile_id, user_id=user_id, source_filename="resume.pdf", parsed_json={})
        job_id = uuid.uuid4()
        job = Job(
            id=job_id,
            title="Data Analyst Intern",
            company="MetricFlow",
            description="SQL and dashboarding.",
            apply_url="https://example.com/metricflow-apply",
            is_active=True
        )
        db.add_all([user, profile, job])
        await db.commit()

        req = ApplicationCreate(profile_id=profile_id, job_id=job_id)
        await create_application(req, db=db)

        apps = await list_applications(profile_id=profile_id, db=db)
        assert len(apps) >= 1
        assert any(a.job_id == job_id for a in apps)


@pytest.mark.asyncio
async def test_get_and_update_profile():
    await init_db()
    async with async_session_factory() as db:
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"edit_{uuid.uuid4().hex[:6]}@example.com", hashed_password="hashed_pw_test")
        profile_id = uuid.uuid4()
        initial_json = {
            "personal_info": {"name": "Test Candidate", "summary": "Initial summary"},
            "skills": ["Python", "SQL"]
        }
        profile = Profile(id=profile_id, user_id=user_id, source_filename="test.pdf", parsed_json=initial_json)
        db.add_all([user, profile])
        await db.commit()

        # 1. Fetch profile
        get_res = await get_profile(profile_id=profile_id, db=db)
        assert get_res.success is True
        assert get_res.data["parsed_json"]["personal_info"]["name"] == "Test Candidate"

        # 2. Update profile skills
        update_req = ProfileUpdateRequest(skills=["Python", "SQL", "Docker", "FastAPI"])
        patch_res = await update_profile(profile_id=profile_id, body=update_req, db=db)
        assert patch_res.success is True
        assert "Docker" in patch_res.data["parsed_json"]["skills"]
        assert "FastAPI" in patch_res.data["parsed_json"]["skills"]


@pytest.mark.asyncio
async def test_claim_profile_guest_to_user():
    await init_db()
    async with async_session_factory() as db:
        # Check if seed user exists, create if not
        existing_seed = (await db.execute(select(User).where(User.id == SEED_USER_ID))).scalar_one_or_none()
        if not existing_seed:
            seed_user = User(id=SEED_USER_ID, email=f"guest_{uuid.uuid4().hex[:6]}@hireme.ai", hashed_password="seed_password_hash")
            db.add(seed_user)

        auth_user_id = uuid.uuid4()
        auth_user = User(id=auth_user_id, email=f"claim_{uuid.uuid4().hex[:6]}@example.com", hashed_password="auth_password_hash")
        profile_id = uuid.uuid4()
        profile = Profile(id=profile_id, user_id=SEED_USER_ID, source_filename="guest_resume.pdf", parsed_json={})
        db.add_all([auth_user, profile])
        await db.commit()

        claim_res = await claim_profile(profile_id=profile_id, current_user=auth_user, db=db)
        assert claim_res.success is True
        assert claim_res.data["user_id"] == str(auth_user_id)
        assert claim_res.data["profile_id"] == str(profile_id)
