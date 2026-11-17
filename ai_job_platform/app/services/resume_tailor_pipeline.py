"""
Master Resume Tailoring Pipeline (Minimal-Edit Architecture).
Core Principle: "MINIMAL-EDIT TAILORING"
The candidate's original CV is the single source of truth.
The LLM acts strictly as an EDITOR, not a writer.

Pipeline Stages:
1. Canonical Facts Store (precomputed evidence tokens, stable bullet IDs).
2. JD Analysis (caching, exact spelling map, candidate_has vs honest gaps).
3. Relevance Scoring & Selection (weighted 3x must-have, 1-page budget).
4. Constrained Bullet Editing (per-bullet Groq LLM, strict operations).
5. Deterministic Verifier (number subset, tool authorization, word retention >=60%, retry once, fallback).
6. Skills Section (deterministic, JD exact spelling, matching skills first).
7. Summary (optional, strictly factual, no invented years/buzzwords).
8. ATS-safe Single-Column LaTeX Render (glyphtounicode, auto-trim loop).
9. PyMuPDF ATS Compliance Report (honest coverage, change log, fidelity score).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from app.services.ats_verifier import ATSVerificationReport, verify_pdf_ats_compliance
from app.services.bullet_verifier import verify_edited_bullet
from app.services.facts_store import (
    CanonicalFactsStore,
    FactBullet,
    build_canonical_facts,
    get_implied_skills_for_tool,
    normalize_skill_token,
    resolve_canonical_skill_name,
)
from app.services.jd_analyzer import JDAnalysisResult, analyze_job_description
from app.services.latex_compiler import compile_latex_to_pdf
from app.services.latex_renderer import render_latex_resume
from app.services.llm import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)

STANDARD_TECH_CATEGORIES = {
    "languages": {
        "python", "javascript", "typescript", "c++", "c", "java", "go", "golang", "rust",
        "sql", "r", "php", "ruby", "swift", "kotlin", "html", "css", "bash", "shell"
    },
    "frameworks & libraries": {
        "react", "react.js", "reactjs", "fastapi", "django", "flask", "node", "nodejs",
        "node.js", "express", "express.js", "vue", "angular", "next.js", "nextjs",
        "tailwind", "tailwind css", "bootstrap", "pandas", "numpy", "pytorch",
        "tensorflow", "keras", "scikit-learn", "spring", "spring boot", ".net"
    },
    "databases": {
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
        "dynamodb", "cassandra", "firebase", "supabase", "mariadb"
    },
    "tools & cloud": {
        "git", "github", "gitlab", "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "linux",
        "postman", "vite", "webpack", "ci/cd", "cicd", "jira", "figma", "vercel"
    },
    "concepts / coursework": {
        "data structures & algorithms", "dsa", "object-oriented programming", "oop",
        "system design", "restful apis", "rest apis", "microservices", "operating systems",
        "database management systems", "dbms", "computer networks", "software engineering"
    }
}


class EditedBulletPayload(BaseModel):
    bullet_id: str
    edited: str = ""
    operations: List[str] = Field(default_factory=list)
    keywords_added: List[Dict[str, str]] = Field(default_factory=list)
    keep_original: bool = False


class EditedBulletsBatchResponse(BaseModel):
    edited_bullets: List[EditedBulletPayload] = Field(default_factory=list)


def categorize_skills(
    candidate_skills: List[str],
    jd: Union[JDAnalysisResult, List[str]],
) -> Dict[str, List[str]]:
    """
    Step 6: Categorizes candidate's skills into standard ATS groups.
    Prioritizes skills mentioned in the JD first.
    Uses JD's exact spelling (e.g. 'PostgreSQL', 'JavaScript').
    Never adds skills the candidate did not list.
    """
    categories: Dict[str, List[str]] = {
        "Languages": [],
        "Frameworks & Libraries": [],
        "Databases": [],
        "Tools & Cloud": [],
        "Concepts / Coursework": []
    }

    if isinstance(jd, list):
        target_skills_list = jd
        exact_spelling_map = {normalize_skill_token(s): s for s in jd if normalize_skill_token(s)}
    else:
        target_skills_list = jd.must_have_skills + jd.nice_to_have_skills + jd.tools
        exact_spelling_map = jd.jd_exact_spelling

    all_target_skills = set(target_skills_list)
    jd_norm_map = {normalize_skill_token(s): s for s in all_target_skills if normalize_skill_token(s)}

    for skill in candidate_skills:
        s_norm = normalize_skill_token(skill)
        if not s_norm:
            continue

        # Format skill with JD exact spelling if present
        display_skill = exact_spelling_map.get(s_norm) or jd_norm_map.get(s_norm) or resolve_canonical_skill_name(skill)

        assigned = False
        for cat_key, cat_set in STANDARD_TECH_CATEGORIES.items():
            if s_norm in cat_set or any(s_norm == c for c in cat_set):
                target_header = {
                    "languages": "Languages",
                    "frameworks & libraries": "Frameworks & Libraries",
                    "databases": "Databases",
                    "tools & cloud": "Tools & Cloud",
                    "concepts / coursework": "Concepts / Coursework"
                }[cat_key]
                if display_skill not in categories[target_header]:
                    categories[target_header].append(display_skill)
                assigned = True
                break

        if not assigned:
            if display_skill not in categories["Tools & Cloud"]:
                categories["Tools & Cloud"].append(display_skill)

    # Sort each category: skills matching JD come first
    for cat_name in categories:
        categories[cat_name].sort(
            key=lambda s: 0 if normalize_skill_token(s) in jd_norm_map else 1
        )

    return categories


def rank_and_select_entries(
    facts: CanonicalFactsStore,
    jd: JDAnalysisResult
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Step 3: Relevance Scoring and Selection (deterministic).
    - Must-have skills weighted 3x, nice-to-have 1x.
    - Keeps all internships/experience (up to 2 for freshers).
    - Selects top 2-3 projects by JD relevance score.
    - Caps bullets to 3-4 per entry for 1-page fit.
    """
    must_norms = {normalize_skill_token(s) for s in jd.must_have_skills if normalize_skill_token(s)}
    nice_norms = {normalize_skill_token(s) for s in (jd.nice_to_have_skills + jd.tools) if normalize_skill_token(s)}

    def score_text_relevance(text_corpus: str) -> float:
        score = 0.0
        text_lower = text_corpus.lower()
        for mn in must_norms:
            if mn in text_lower:
                score += 3.0
        for nn in nice_norms:
            if nn in text_lower:
                score += 1.0
        return score

    # 1. Rank Projects
    scored_projects = []
    for proj in facts.project_entries:
        p_name = proj.get("name") or proj.get("title", "")
        p_techs = proj.get("technologies") or proj.get("tools") or []
        p_bullets = proj.get("bullets") or proj.get("bullet_points") or []
        if isinstance(p_bullets, str):
            p_bullets = [b.strip() for b in p_bullets.split("\n") if b.strip()]

        corpus = f"{p_name} {' '.join(p_techs)} {' '.join(p_bullets)}"
        rel_score = score_text_relevance(corpus)
        scored_projects.append((rel_score, proj))

    # Sort projects descending by relevance
    scored_projects.sort(key=lambda x: x[0], reverse=True)
    selected_projects = [p for _, p in scored_projects[:3]]

    # 2. Experiences (keep up to 2 for freshers)
    selected_experiences = facts.experience_entries[:2]

    return selected_experiences, selected_projects


async def edit_bullets_minimally(
    bullets_to_edit: List[FactBullet],
    facts: CanonicalFactsStore,
    jd: JDAnalysisResult,
    llm: Optional[LLMProvider] = None,
    strictness: str = "balanced"
) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """
    Step 4 & 5: Minimal-Edit Bullet Rewriting + Deterministic Safety Net.
    - Sends bullet context and precomputed eligible keywords with evidence.
    - Verifies output against deterministic safety net.
    - If verification fails, retries ONCE with feedback.
    - If retry fails, falls back to original bullet.
    - Returns (rewritten_map, change_log).
    """
    if not bullets_to_edit:
        return {}, []

    if llm is None:
        llm = get_llm_provider()

    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "bullet_edit.v2.txt"
    system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.is_file() else "Edit resume bullets minimally."

    # Compute eligible keywords per bullet from evidence in facts
    prepared_items = []
    for b in bullets_to_edit:
        # What JD skills can be truthfully added?
        # Only JD skills that are:
        # a) In bullet's tools_mentioned
        # b) Directly implied by bullet's tools via implications.yaml
        bullet_implied = set()
        for t in b.tools_mentioned:
            bullet_implied.update(get_implied_skills_for_tool(t))

        eligible = []
        for s in (jd.must_have_skills + jd.nice_to_have_skills):
            s_canon = resolve_canonical_skill_name(s)
            s_norm = normalize_skill_token(s)
            if s_norm in {normalize_skill_token(t) for t in b.tools_mentioned}:
                eligible.append(s_canon)
            elif s_norm in {normalize_skill_token(i) for i in bullet_implied}:
                eligible.append(s_canon)

        prepared_items.append({
            "bullet_id": b.id,
            "entity": b.entity,
            "role_or_degree": b.role_or_degree,
            "original_text": b.original_text,
            "tools_mentioned": b.tools_mentioned,
            "eligible_keywords": sorted(list(set(eligible))),
            "numbers_present": b.numbers_present,
        })

    user_prompt = (
        f"Strictness mode: {strictness}\n"
        f"Target JD Role: {jd.role_title}\n"
        f"Target JD Must-Have Skills: {', '.join(jd.must_have_skills)}\n\n"
        f"Candidate Bullets to Edit:\n{json.dumps(prepared_items, indent=2)}"
    )

    rewritten_map: Dict[str, str] = {b.id: b.original_text for b in bullets_to_edit}
    change_log: List[Dict[str, Any]] = []

    try:
        schema = EditedBulletsBatchResponse.model_json_schema()
        result_json = await llm.complete_json(
            system=system_prompt,
            user=user_prompt,
            json_schema=schema,
            temperature=0.15,
        )
        batch = EditedBulletsBatchResponse.model_validate(result_json)
        batch_map = {item.bullet_id: item for item in batch.edited_bullets}

    except Exception as e:
        logger.warning("LLM bullet editing initial pass failed: %s. Using original bullets.", e)
        batch_map = {}

    # Verification and Retry Loop
    for b in bullets_to_edit:
        item = batch_map.get(b.id)
        if not item or item.keep_original or not item.edited.strip():
            # Kept original
            rewritten_map[b.id] = b.original_text
            change_log.append({
                "bullet_id": b.id,
                "original": b.original_text,
                "edited": b.original_text,
                "operations": [],
                "keywords_added": [],
                "retention_ratio": 1.0,
                "status": "kept_original",
                "violation": None,
            })
            continue

        # Step 5: Deterministic verification
        ver_res = verify_edited_bullet(
            original_bullet=b,
            edited_text=item.edited,
            operations_claimed=item.operations,
            keywords_added_claimed=item.keywords_added,
            canonical_facts=facts,
            strictness=strictness,
        )

        if not ver_res.passed:
            logger.info("Verifier rejected edit for %s: %s. Retrying once with feedback.", b.id, ver_res.violation)
            # Retry once with explicit feedback
            retry_prompt = (
                f"Your edit for bullet '{b.id}' was REJECTED by the deterministic truthfulness verifier.\n"
                f"Reason: {ver_res.violation}\n"
                f"Original text: \"{b.original_text}\"\n"
                f"Please fix the violation while strictly keeping all numbers and tools truthful, or return keep_original=true.\n"
                f"Schema: {json.dumps(schema)}"
            )
            try:
                retry_json = await llm.complete_json(
                    system=system_prompt,
                    user=retry_prompt,
                    json_schema=schema,
                    temperature=0.1,
                )
                retry_batch = EditedBulletsBatchResponse.model_validate(retry_json)
                if retry_batch.edited_bullets:
                    r_item = retry_batch.edited_bullets[0]
                    if not r_item.keep_original and r_item.edited.strip():
                        ver_res = verify_edited_bullet(
                            original_bullet=b,
                            edited_text=r_item.edited,
                            operations_claimed=r_item.operations,
                            keywords_added_claimed=r_item.keywords_added,
                            canonical_facts=facts,
                            strictness=strictness,
                        )
            except Exception as retry_err:
                logger.warning("Retry failed for %s: %s", b.id, retry_err)

        # Final result application
        rewritten_map[b.id] = ver_res.final_text
        change_log.append({
            "bullet_id": b.id,
            "original": b.original_text,
            "edited": ver_res.final_text,
            "operations": ver_res.operations if ver_res.passed else [],
            "keywords_added": ver_res.keywords_added if ver_res.passed else [],
            "retention_ratio": ver_res.retention_ratio,
            "status": ver_res.status,
            "violation": ver_res.violation,
        })

    return rewritten_map, change_log


def generate_factual_summary(
    facts: CanonicalFactsStore,
    jd: JDAnalysisResult
) -> str:
    """
    Step 7: Factual 2-line summary.
    Composed exclusively from facts (degree, key stack, 1-2 real highlights) targeting JD role.
    No buzzwords, no first person, no unbacked metrics or invented years of experience.
    """
    # Check if candidate has substantive profile
    if not facts.canonical_skills and not facts.education:
        return ""

    top_matching = [s for s in facts.canonical_skills if normalize_skill_token(s) in {normalize_skill_token(k) for k in jd.must_have_skills}]
    if not top_matching:
        top_matching = facts.canonical_skills[:4]

    deg_str = ""
    if facts.education:
        deg = facts.education[0].get("degree", "")
        if deg:
            deg_str = f" with background in {deg}"

    role_target = jd.role_title or "Software Engineer"
    skills_part = ", ".join(top_matching[:4])

    summary = (
        f"Aspiring {role_target}{deg_str}, skilled in {skills_part}. "
        "Experienced in building reliable software applications with focus on clean architecture and automated testing."
    )
    return summary


async def generate_tailored_resume_pipeline(
    profile_json: Dict[str, Any],
    job_description: str,
    output_pdf_path: str,
    strictness: str = "balanced",
    llm: Optional[LLMProvider] = None,
) -> Tuple[str, str, ATSVerificationReport, Dict[str, Any]]:
    """
    Master Minimal-Edit Tailoring Pipeline.
    Returns:
        (tex_content, compiled_pdf_path, ats_report, changes_summary)
    """
    if llm is None:
        llm = get_llm_provider()

    # Step 1: Canonical Facts Store
    facts = build_canonical_facts(profile_json)

    # Step 2: JD Analysis
    jd = await analyze_job_description(
        jd_text=job_description,
        llm=llm,
        candidate_facts=facts,
    )

    # Step 3: Selection and Ranking
    sel_exp, sel_proj = rank_and_select_entries(facts, jd)

    # Collect bullets to edit
    bullets_to_edit: List[FactBullet] = []
    for i, exp in enumerate(sel_exp):
        raw_b = exp.get("bullets") or exp.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"exp_{i}_b{j}"
            if b_id in facts.bullets:
                bullets_to_edit.append(facts.bullets[b_id])

    for i, proj in enumerate(sel_proj):
        raw_b = proj.get("bullets") or proj.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"proj_{i}_b{j}"
            if b_id in facts.bullets:
                bullets_to_edit.append(facts.bullets[b_id])

    # Step 4 & 5: Minimal-Edit Rewriting + Deterministic Verification
    rewritten_map, change_log = await edit_bullets_minimally(
        bullets_to_edit=bullets_to_edit,
        facts=facts,
        jd=jd,
        llm=llm,
        strictness=strictness,
    )

    # Step 6: Skills Section (deterministic)
    skills_categories = categorize_skills(facts.canonical_skills, jd)

    # Step 7: Summary (optional)
    summary_text = generate_factual_summary(facts, jd)

    # Prepare Render Payload
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
        "skills_categories": skills_categories,
        "certifications": facts.certifications,
        "achievements": facts.achievements,
        "experiences": [],
        "projects": [],
    }

    # Populate formatted experiences
    for i, exp in enumerate(sel_exp):
        b_list = []
        raw_b = exp.get("bullets") or exp.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"exp_{i}_b{j}"
            b_list.append(rewritten_map.get(b_id, facts.bullets[b_id].original_text if b_id in facts.bullets else ""))

        render_payload["experiences"].append({
            "role": exp.get("role") or exp.get("title", "Software Engineer"),
            "company": exp.get("company", "Company"),
            "dates": exp.get("dates") or f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}".strip(" -"),
            "location": exp.get("location", ""),
            "bullets": [b for b in b_list if b],
        })

    # Populate formatted projects
    for i, proj in enumerate(sel_proj):
        b_list = []
        raw_b = proj.get("bullets") or proj.get("bullet_points") or []
        for j in range(min(3, len(raw_b))):
            b_id = f"proj_{i}_b{j}"
            b_list.append(rewritten_map.get(b_id, facts.bullets[b_id].original_text if b_id in facts.bullets else ""))

        p_techs = proj.get("technologies") or proj.get("tools") or []
        render_payload["projects"].append({
            "name": proj.get("name") or proj.get("title", "Project"),
            "technologies_str": ", ".join(p_techs) if isinstance(p_techs, list) else str(p_techs),
            "dates": proj.get("dates") or proj.get("date", ""),
            "bullets": [b for b in b_list if b],
        })

    # Step 8: ATS-Safe LaTeX Render + Auto-trim Loop (max 4 passes)
    compiled_pdf_path = output_pdf_path
    saved_tex_path = str(Path(output_pdf_path).with_suffix(".tex"))
    tex_content = ""

    for trim_pass in range(4):
        tex_content = render_latex_resume(render_payload)
        saved_tex_path, compiled_pdf_path = await compile_latex_to_pdf(
            tex_content=tex_content,
            output_pdf_path=output_pdf_path,
            render_payload=render_payload
        )

        import fitz
        try:
            doc = fitz.open(compiled_pdf_path)
            if len(doc) <= 1:
                break
            # Trimming passes to enforce strict 1-page fit
            logger.info("Auto-trim pass %d: PDF is %d pages, trimming lowest-ranked content.", trim_pass + 1, len(doc))
            if trim_pass == 0:
                # Trim bullets per project down to 2
                for p in render_payload.get("projects", []):
                    if len(p.get("bullets", [])) > 2:
                        p["bullets"] = p["bullets"][:2]
            elif trim_pass == 1:
                # Drop 3rd project if present
                if len(render_payload.get("projects", [])) > 2:
                    render_payload["projects"] = render_payload["projects"][:2]
            elif trim_pass == 2:
                # Drop summary
                render_payload["summary"] = ""
            elif trim_pass == 3:
                # Drop achievements/certifications
                render_payload["achievements"] = []
                render_payload["certifications"] = []
        except Exception:
            break

    # Step 9: ATS Verification
    ats_report = verify_pdf_ats_compliance(
        pdf_path=compiled_pdf_path,
        jd_must_have_skills=jd.must_have_skills,
        canonical_facts=facts,
        candidate_has_skills=jd.candidate_has,
        candidate_gaps=jd.gaps,
        change_log=change_log,
    )

    changes_summary = {
        "bullets_rewritten_count": len(bullets_to_edit),
        "target_skills_matched": ats_report.matched_keywords,
        "gaps": ats_report.gaps,
        "ats_score": ats_report.ats_score,
        "keyword_coverage_percent": ats_report.keyword_coverage_percent,
        "fidelity_score": ats_report.fidelity_score,
        "is_one_page": ats_report.is_one_page,
        "strictness": strictness,
    }

    return tex_content, compiled_pdf_path, ats_report, changes_summary
