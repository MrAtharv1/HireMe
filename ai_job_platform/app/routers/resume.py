"""
Resume Router — all generic resume-related HTTP endpoints.

Endpoints
---------
POST /resume/upload          — upload & parse a resume file
POST /resume/ats-score       — score a profile against a JD
POST /resume/tailor          — generic tailor + generate PDF
GET  /resume/profile/{id}    — fetch a parsed profile
GET  /resume/download/{id}   — download a generated PDF
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_optional_current_user, get_current_user
from app.models.db_models import Job, Profile, ResumeVersion, User
from app.schemas.dto import (
    APIResponse,
    ATSScoreRequest,
    ATSScoreResponse,
    RecompileRequest,
    ResumeUploadResponse,
    TailorRequest,
    TailorResponse,
)
from app.services.resume_service import (
    evaluate_ats,
    process_resume_upload,
    recompile_resume_version,
    tailor_and_generate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ─────────────────────────────────────────────────────────────────────────
#  POST /resume/upload
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or image)"),
    user_id: Optional[uuid.UUID] = Query(None, description="ID of the owning user"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume document. The backend will:
    1. Extract text (with OCR fallback for scanned docs).
    2. Parse the text into structured JSON via Gemini.
    3. Persist the profile to the database under the authenticated user.
    """
    effective_user_id = current_user.id if current_user else (user_id or uuid.UUID("123e4567-e89b-12d3-a456-426614174004"))
    # ── Validate file ────────────────────────────────────────────────────
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit.",
        )
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ── Process ──────────────────────────────────────────────────────────
    try:
        profile, parsed, raw_text, method = await process_resume_upload(
            file_bytes=file_bytes,
            filename=filename,
            user_id=effective_user_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Resume upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {exc}",
        )

    return ResumeUploadResponse(
        profile_id=profile.id,
        parsed_resume=parsed,
        raw_text_length=len(raw_text),
        extraction_method=method,
    )


# ─────────────────────────────────────────────────────────────────────────
#  POST /resume/ats-score
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/ats-score",
    response_model=ATSScoreResponse,
    summary="ATS-score a profile against a job description",
)
async def ats_score(
    body: ATSScoreRequest,
    profile_id: uuid.UUID = Query(..., description="Saved profile ID"),
    job_id: uuid.UUID = Query(..., description="Job listing ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Score a candidate's structured profile against a job description.
    Returns an ATS score (0-100), missing keywords, strengths, and fixes.
    """
    # Validate that profile and job exist
    profile = (await db.execute(select(Profile).where(Profile.id == profile_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    try:
        result = await evaluate_ats(
            profile_id=profile_id,
            job_id=job_id,
            job_description=body.job_description,
            db=db,
        )
    except Exception as exc:
        logger.exception("ATS scoring failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS scoring failed: {exc}",
        )

    return result


# ─────────────────────────────────────────────────────────────────────────
#  POST /resume/tailor
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/tailor",
    response_model=TailorResponse,
    summary="Tailor a resume to a JD and generate LaTeX/PDF",
)
async def tailor(
    body: TailorRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional ID of the owning user"),
    job_id: uuid.UUID | None = Query(None, description="Optional job ID"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generic endpoint to tailor a resume's bullet points and summary to a specific job description,
    then generate a downloadable LaTeX source and PDF using minimal-edit principles.
    Persists the tailored version under the user's permanent account.
    """
    effective_user_id = current_user.id if current_user else (user_id or uuid.UUID("123e4567-e89b-12d3-a456-426614174004"))
    try:
        version, summary = await tailor_and_generate(
            profile_json=body.profile_json,
            job_description=body.job_description,
            user_id=effective_user_id,
            job_id=job_id,
            db=db,
            strictness=body.strictness or "balanced",
        )
    except Exception as exc:
        logger.exception("Tailoring failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tailoring failed: {exc}",
        )

    ats_dict = version.ats_report or {}
    return TailorResponse(
        version_id=version.id,
        tailored_json=version.tailored_json,
        pdf_path=version.pdf_path or f"/api/v1/resume/{version.id}/tex",
        ats_score=version.ats_score,
        ats_report=ats_dict,
        change_log=ats_dict.get("change_log", []),
        matched_keywords=ats_dict.get("matched_keywords", []),
        gaps=ats_dict.get("gaps", []),
        coverage_percent=ats_dict.get("keyword_coverage_percent"),
        fidelity_score=ats_dict.get("fidelity_score"),
    )


@router.post(
    "/{version_id}/recompile",
    response_model=TailorResponse,
    summary="Recompile resume version with bullet overrides (Accept/Revert)",
)
async def recompile_resume(
    version_id: uuid.UUID,
    body: RecompileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Recompiles an existing resume with user bullet accept/revert overrides and updates PDF/report."""
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found.")

    try:
        updated_version, ats_dict = await recompile_resume_version(
            version=version,
            bullet_overrides=body.bullet_overrides,
            db=db,
            strictness=body.strictness or "balanced",
        )
    except Exception as exc:
        logger.exception("Recompile failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recompilation failed: {exc}",
        )

    return TailorResponse(
        version_id=updated_version.id,
        tailored_json=updated_version.tailored_json,
        pdf_path=updated_version.pdf_path or f"/api/v1/resume/{updated_version.id}/tex",
        ats_score=updated_version.ats_score,
        ats_report=ats_dict,
        change_log=ats_dict.get("change_log", []),
        matched_keywords=ats_dict.get("matched_keywords", []),
        gaps=ats_dict.get("gaps", []),
        coverage_percent=ats_dict.get("keyword_coverage_percent"),
        fidelity_score=ats_dict.get("fidelity_score"),
    )


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/{version_id}/tex
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/{version_id}/tex",
    summary="Download generated LaTeX (.tex) source",
)
async def download_tex(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns the raw LaTeX source code for the tailored resume."""
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found.")

    if version.tex_content:
        from fastapi.responses import Response
        return Response(
            content=version.tex_content,
            media_type="application/x-tex",
            headers={"Content-Disposition": f"attachment; filename=resume_{version.id}.tex"}
        )

    if version.tex_path and Path(version.tex_path).is_file():
        return FileResponse(
            path=version.tex_path,
            media_type="application/x-tex",
            filename=f"resume_{version.id}.tex"
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LaTeX source file not found.")


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/{version_id}/pdf
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/{version_id}/pdf",
    summary="Download generated resume PDF",
)
async def download_pdf_direct(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download the compiled PDF for a given ResumeVersion."""
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found.")

    if not version.pdf_path or not Path(version.pdf_path).is_file():
        # Attempt on-the-fly rendering so the preview works seamlessly
        from app.services.latex_compiler import render_pdf_fallback
        output_dir = Path("storage/resumes")
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(output_dir / f"tailored_{version.user_id}_{version.id.hex[:8]}.pdf")

        try:
            render_pdf_fallback(
                output_pdf_path=pdf_path,
                tex_content=version.tex_content,
            )
            version.pdf_path = pdf_path
            await db.commit()
        except Exception as exc:
            logger.error("On-the-fly PDF compilation failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {exc}"
            )

    pdf = Path(version.pdf_path)
    return FileResponse(
        path=str(pdf),
        media_type="application/pdf",
        filename=pdf.name,
    )


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/my-versions — User's saved tailored resumes
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/my-versions",
    response_model=APIResponse,
    summary="Get all tailored resume versions belonging to current user",
)
async def get_my_versions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all tailored resume snapshots belonging to the authenticated user."""
    result = await db.execute(
        select(ResumeVersion)
        .where(ResumeVersion.user_id == current_user.id)
        .order_by(ResumeVersion.created_at.desc())
    )
    versions = result.scalars().all()
    data = [
        {
            "id": str(v.id),
            "job_id": str(v.job_id) if v.job_id else None,
            "version_label": v.version_label or "Tailored Resume",
            "ats_score": v.ats_score,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "has_pdf": bool(v.pdf_path and Path(v.pdf_path).is_file()),
        }
        for v in versions
    ]
    return APIResponse(success=True, message=f"Retrieved {len(data)} resume versions.", data=data)


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/profile/{profile_id}
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/profile/{profile_id}",
    response_model=APIResponse,
    summary="Retrieve a parsed profile",
)
async def get_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously parsed profile by its ID."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    return APIResponse(
        data={
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "source_filename": profile.source_filename,
            "parsed_json": profile.parsed_json,
            "created_at": profile.created_at.isoformat(),
        }
    )


@router.put(
    "/profile/{profile_id}",
    response_model=APIResponse,
    summary="Update candidate profile facts before tailoring",
)
async def update_profile(
    profile_id: uuid.UUID,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Updates candidate ground-truth facts (parsed_json) prior to tailoring."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    profile.parsed_json = body
    await db.commit()
    await db.refresh(profile)

    return APIResponse(
        data={
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "source_filename": profile.source_filename,
            "parsed_json": profile.parsed_json,
            "created_at": profile.created_at.isoformat(),
        }
    )


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/download/{version_id}
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/download/{version_id}",
    summary="Download a generated resume PDF",
)
async def download_pdf(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Stream the generated PDF for a given ResumeVersion."""
    result = await db.execute(
        select(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version or not version.pdf_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found.")

    pdf = Path(version.pdf_path)
    if not pdf.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file missing from storage.",
        )

    return FileResponse(
        path=str(pdf),
        media_type="application/pdf",
        filename=pdf.name,
    )


# ─────────────────────────────────────────────────────────────────────────
#  GET /resume/my-versions — User's saved tailored resumes
# ─────────────────────────────────────────────────────────────────────────

@router.get(
    "/my-versions",
    response_model=APIResponse,
    summary="Get all tailored resume versions belonging to current user",
)
async def get_my_versions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all tailored resume snapshots belonging to the authenticated user."""
    result = await db.execute(
        select(ResumeVersion)
        .where(ResumeVersion.user_id == current_user.id)
        .order_by(ResumeVersion.created_at.desc())
    )
    versions = result.scalars().all()
    data = [
        {
            "id": str(v.id),
            "job_id": str(v.job_id) if v.job_id else None,
            "version_label": v.version_label or "Tailored Resume",
            "ats_score": v.ats_score,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "has_pdf": bool(v.pdf_path and Path(v.pdf_path).is_file()),
        }
        for v in versions
    ]
    return APIResponse(success=True, message=f"Retrieved {len(data)} resume versions.", data=data)