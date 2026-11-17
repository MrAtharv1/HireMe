"""
Resume Service — orchestrates extraction, parsing, scoring, and PDF generation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Match, Profile, ResumeVersion
from app.schemas.dto import ATSScoreResponse, ParsedResume
from app.services.ai_service import parse_resume_text, score_ats, tailor_resume
from app.utils.extractor import extract_text
from app.utils.pdf_gen import generate_pdf

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
#  1. Upload & Parse
# ─────────────────────────────────────────────────────────────────────────

async def process_resume_upload(
    file_bytes: bytes,
    filename: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Tuple[Profile, ParsedResume, str, str]:
    """
    Full pipeline: extract text → AI parse → persist Profile.

    Returns
    -------
    (Profile, ParsedResume, raw_text, extraction_method)
    """
    raw_text, method = await extract_text(file_bytes, filename)
    logger.info("Extracted %d chars from '%s' via %s", len(raw_text), filename, method)

    parsed = await parse_resume_text(raw_text)

    parsed.resume_meta.file_name = filename
    parsed.resume_meta.extraction_method = method
    parsed.resume_meta.parsed_at = datetime.now(timezone.utc).isoformat()

    profile = Profile(
        user_id=user_id,
        source_filename=filename,
        raw_text=raw_text,
        parsed_json=parsed.model_dump(),
    )
    db.add(profile)
    await db.flush()  
    await db.refresh(profile)

    return profile, parsed, raw_text, method


# ─────────────────────────────────────────────────────────────────────────
#  2. ATS Scoring
# ─────────────────────────────────────────────────────────────────────────

async def evaluate_ats(
    profile_id: uuid.UUID,
    job_id: uuid.UUID,
    job_description: str,
    db: AsyncSession,
) -> ATSScoreResponse:
    """
    Score a saved profile against a job description and persist the Match.
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ValueError(f"Profile {profile_id} not found.")

    profile_json: Dict[str, Any] = profile.parsed_json  
    ats = await score_ats(profile_json, job_description)

    match = Match(
        profile_id=profile_id,
        job_id=job_id,
        ats_score=ats.ats_score,
        missing_keywords=ats.missing_keywords,
        strengths=ats.strengths,
        fixes=ats.fixes,
    )
    db.add(match)
    await db.flush()

    return ats


# ─────────────────────────────────────────────────────────────────────────
#  3. Tailor & Generate PDF (LaTeX Pipeline)
# ─────────────────────────────────────────────────────────────────────────

async def tailor_and_generate(
    profile_json: Dict[str, Any],
    job_description: str,
    user_id: uuid.UUID,
    job_id: uuid.UUID | None,
    db: AsyncSession,
    strictness: str = "balanced",
) -> Tuple[ResumeVersion, Dict[str, Any]]:
    """
    Tailor a resume to a JD using the minimal-edit ATS pipeline.
    Persists ResumeVersion with tex_path, tex_content, pdf_path, ats_score, and ats_report.
    Returns (ResumeVersion, changes_summary)
    """
    from app.services.resume_tailor_pipeline import generate_tailored_resume_pipeline
    from app.services.latex_compiler import compile_latex_to_pdf, render_pdf_fallback
    from app.services.latex_renderer import render_latex_resume
    from app.services.facts_store import build_canonical_facts
    from app.services.jd_analyzer import analyze_job_description

    output_dir = Path("storage/resumes")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"tailored_{user_id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = str(output_dir / pdf_filename)
    tex_path = str(output_dir / f"{Path(pdf_filename).stem}.tex")

    tex_content, compiled_pdf, ats_report, summary = await generate_tailored_resume_pipeline(
        profile_json=profile_json,
        job_description=job_description,
        output_pdf_path=pdf_path,
        strictness=strictness,
    )
    ats_score = ats_report.ats_score
    ats_report_dict = ats_report.model_dump()

    version = ResumeVersion(
        user_id=user_id,
        job_id=job_id,
        tailored_json=profile_json,
        pdf_path=compiled_pdf,
        tex_path=tex_path,
        tex_content=tex_content,
        ats_score=ats_score,
        ats_report=ats_report_dict,
        version_label=f"Tailored ({strictness.capitalize()}) — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
    )
    db.add(version)
    await db.flush()

    return version, summary


async def recompile_resume_version(
    version: ResumeVersion,
    bullet_overrides: Dict[str, str],
    db: AsyncSession,
    strictness: str = "balanced",
) -> Tuple[ResumeVersion, Dict[str, Any]]:
    """
    Recompiles an existing ResumeVersion with user-accepted or reverted bullet overrides.
    Re-renders LaTeX, recompiles PDF, re-runs ATS verifier, and commits to DB.
    """
    from app.services.facts_store import build_canonical_facts
    from app.services.jd_analyzer import analyze_job_description
    from app.services.resume_tailor_pipeline import (
        rank_and_select_entries,
        categorize_skills,
        generate_factual_summary,
    )
    from app.services.latex_compiler import compile_latex_to_pdf
    from app.services.latex_renderer import render_latex_resume
    from app.services.ats_verifier import verify_pdf_ats_compliance

    profile_json = dict(version.tailored_json or {})
    job_desc = ""
    if version.job_id:
        from app.models.db_models import Job
        job_obj = (await db.execute(select(Job).where(Job.id == version.job_id))).scalar_one_or_none()
        if job_obj and job_obj.description:
            job_desc = job_obj.description

    facts = build_canonical_facts(profile_json)
    jd = await analyze_job_description(job_desc or "Software Engineer", candidate_facts=facts)
    sel_exp, sel_proj = rank_and_select_entries(facts, jd)
    skills_cats = categorize_skills(facts.canonical_skills, jd)
    summary_text = generate_factual_summary(facts, jd)

    render_payload: Dict[str, Any] = {
        "name": facts.name or "Software Engineer",
        "email": facts.email,
        "phone": facts.phone,
        "location": facts.location,
        "linkedin": facts.linkedin,
        "github": facts.github,
        "portfolio": facts.portfolio,
        "summary": summary_text,
        "education": facts.education,
        "skills_categories": skills_cats,
        "certifications": facts.certifications,
        "achievements": facts.achievements,
        "experiences": [],
        "projects": [],
    }

    # Apply overrides or fallback to original/current
    change_log = (version.ats_report or {}).get("change_log", [])
    change_log_map = {item["bullet_id"]: item for item in change_log if "bullet_id" in item}

    for i, exp in enumerate(sel_exp):
        b_list = []
        raw_b = exp.get("bullets") or exp.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"exp_{i}_b{j}"
            if b_id in bullet_overrides:
                b_text = bullet_overrides[b_id]
            elif b_id in change_log_map:
                b_text = change_log_map[b_id].get("edited", facts.bullets[b_id].original_text if b_id in facts.bullets else "")
            else:
                b_text = facts.bullets[b_id].original_text if b_id in facts.bullets else ""
            b_list.append(b_text)

        render_payload["experiences"].append({
            "role": exp.get("role") or exp.get("title", "Software Engineer"),
            "company": exp.get("company", "Company"),
            "dates": exp.get("dates") or f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}".strip(" -"),
            "location": exp.get("location", ""),
            "bullets": [b for b in b_list if b],
        })

    for i, proj in enumerate(sel_proj):
        b_list = []
        raw_b = proj.get("bullets") or proj.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"proj_{i}_b{j}"
            if b_id in bullet_overrides:
                b_text = bullet_overrides[b_id]
            elif b_id in change_log_map:
                b_text = change_log_map[b_id].get("edited", facts.bullets[b_id].original_text if b_id in facts.bullets else "")
            else:
                b_text = facts.bullets[b_id].original_text if b_id in facts.bullets else ""
            b_list.append(b_text)

        p_techs = proj.get("technologies") or proj.get("tools") or []
        render_payload["projects"].append({
            "name": proj.get("name") or proj.get("title", "Project"),
            "technologies_str": ", ".join(p_techs) if isinstance(p_techs, list) else str(p_techs),
            "dates": proj.get("dates") or proj.get("date", ""),
            "bullets": [b for b in b_list if b],
        })

    tex_content = render_latex_resume(render_payload)
    output_pdf = version.pdf_path or f"storage/resumes/tailored_{version.user_id}_{version.id.hex[:8]}.pdf"
    saved_tex_path, compiled_pdf_path = await compile_latex_to_pdf(
        tex_content=tex_content,
        output_pdf_path=output_pdf,
        render_payload=render_payload,
    )

    # Re-verify
    ats_report = verify_pdf_ats_compliance(
        pdf_path=compiled_pdf_path,
        jd_must_have_skills=jd.must_have_skills,
        canonical_facts=facts,
        candidate_has_skills=jd.candidate_has,
        candidate_gaps=jd.gaps,
        change_log=change_log,
    )

    version.tex_content = tex_content
    version.pdf_path = compiled_pdf_path
    version.ats_score = ats_report.ats_score
    version.ats_report = ats_report.model_dump()
    await db.commit()

    return version, ats_report.model_dump()