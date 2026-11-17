"""
Job Description Analyzer Service (Step 2).
Extracts structured technical requirements:
- role_title, must_have_skills, nice_to_have_skills, tools, domain_keywords, responsibilities, experience_level.
- Normalizes every skill via synonym map and records JD exact spelling.
- Computes candidate_has (direct or via implications.yaml) vs gaps deterministically.
- Caches analysis by SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from app.services.facts_store import (
    CanonicalFactsStore,
    SYNONYMS_MAP,
    normalize_skill_token,
    resolve_canonical_skill_name,
)
from app.services.llm import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)


class JDAnalysisResult(BaseModel):
    role_title: str = "Software Engineer"
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domain_keywords: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    experience_level: str = "0-2 years"
    jd_exact_spelling: Dict[str, str] = Field(default_factory=dict)
    candidate_has: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


# In-memory analysis cache
_JD_CACHE: Dict[str, JDAnalysisResult] = {}


def _compute_jd_hash(text: str) -> str:
    cleaned = (text or "").strip().lower()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def _load_prompt_template() -> str:
    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "jd_analysis.v2.txt"
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    return (
        "Extract role_title, must_have_skills, nice_to_have_skills, tools, "
        "domain_keywords, responsibilities, experience_level in valid JSON."
    )


def compute_candidate_skills_and_gaps(
    jd_skills: List[str],
    facts: CanonicalFactsStore
) -> Tuple[List[str], List[str]]:
    """
    Computes which JD skills the candidate truly possesses (directly or via implications.yaml)
    versus skills the candidate lacks (gaps). Never fabricates skills the candidate lacks.
    """
    cand_tokens = set(facts.normalized_skills)
    # Also expand implied skills
    implied_skills = facts.get_implied_skills()
    for imp in implied_skills:
        cand_tokens.add(normalize_skill_token(imp))

    candidate_has: List[str] = []
    gaps: List[str] = []

    for skill in jd_skills:
        s_norm = normalize_skill_token(skill)
        if not s_norm:
            continue
        # Direct match or substring/implication match
        has_skill = (
            s_norm in cand_tokens
            or any(s_norm in c for c in cand_tokens)
            or any(c in s_norm for c in cand_tokens if len(c) > 3)
        )
        if has_skill:
            if skill not in candidate_has:
                candidate_has.append(skill)
        else:
            if skill not in gaps:
                gaps.append(skill)

    return candidate_has, gaps


async def analyze_job_description(
    jd_text: str,
    llm: Optional[LLMProvider] = None,
    candidate_facts: Optional[CanonicalFactsStore] = None,
    use_cache: bool = True
) -> JDAnalysisResult:
    """
    Analyzes job description and extracts structured keywords with caching.
    """
    if not jd_text:
        return JDAnalysisResult()

    jd_hash = _compute_jd_hash(jd_text)
    if use_cache and jd_hash in _JD_CACHE:
        cached = _JD_CACHE[jd_hash]
        if candidate_facts:
            has_skills, gap_skills = compute_candidate_skills_and_gaps(
                cached.must_have_skills + cached.nice_to_have_skills, candidate_facts
            )
            cached.candidate_has = has_skills
            cached.gaps = gap_skills
        return cached

    if llm is None:
        llm = get_llm_provider()

    system_prompt = _load_prompt_template()
    # Truncate JD to ~2500 chars to respect rate limits
    safe_jd = jd_text[:2500] if len(jd_text) > 2500 else jd_text
    user_prompt = f"Analyze this job description and output valid JSON only:\n\n{safe_jd}"

    try:
        class LLMJDOutput(BaseModel):
            role_title: str = "Software Engineer"
            must_have_skills: List[str] = Field(default_factory=list)
            nice_to_have_skills: List[str] = Field(default_factory=list)
            tools: List[str] = Field(default_factory=list)
            domain_keywords: List[str] = Field(default_factory=list)
            responsibilities: List[str] = Field(default_factory=list)
            experience_level: str = "0-2 years"

        schema = LLMJDOutput.model_json_schema()
        result_json = await llm.complete_json(
            system=system_prompt,
            user=user_prompt,
            json_schema=schema,
            temperature=0.1,
        )
        raw_output = LLMJDOutput.model_validate(result_json)
        
        # Build exact spelling map and normalize lists
        spelling_map: Dict[str, str] = {}
        all_raw_skills = raw_output.must_have_skills + raw_output.nice_to_have_skills + raw_output.tools
        for s in all_raw_skills:
            if s and isinstance(s, str):
                s_clean = s.strip()
                norm = normalize_skill_token(s_clean)
                if norm and norm not in spelling_map:
                    spelling_map[norm] = s_clean

        analysis = JDAnalysisResult(
            role_title=raw_output.role_title or "Software Engineer",
            must_have_skills=raw_output.must_have_skills,
            nice_to_have_skills=raw_output.nice_to_have_skills,
            tools=raw_output.tools,
            domain_keywords=raw_output.domain_keywords,
            responsibilities=raw_output.responsibilities,
            experience_level=raw_output.experience_level,
            jd_exact_spelling=spelling_map,
        )

    except Exception as e:
        logger.warning("LLM JD analysis failed: %s. Using heuristic keyword extraction.", e)
        # Heuristic fallback
        words = re.findall(r"\b[A-Za-z0-9+#.-]{2,20}\b", jd_text)
        common_tech = ["Python", "FastAPI", "React", "SQL", "PostgreSQL", "Docker", "AWS", "Git", "JavaScript", "TypeScript"]
        found = [t for t in common_tech if t.lower() in jd_text.lower()]
        spelling_map = {normalize_skill_token(t): t for t in found}
        analysis = JDAnalysisResult(
            role_title="Software Engineer",
            must_have_skills=found[:5],
            nice_to_have_skills=found[5:],
            tools=found,
            domain_keywords=["Engineering"],
            jd_exact_spelling=spelling_map,
        )

    if candidate_facts:
        has_skills, gap_skills = compute_candidate_skills_and_gaps(
            analysis.must_have_skills + analysis.nice_to_have_skills, candidate_facts
        )
        analysis.candidate_has = has_skills
        analysis.gaps = gap_skills

    if use_cache:
        _JD_CACHE[jd_hash] = analysis

    return analysis
