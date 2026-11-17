"""
Job Classifier Service — 3-Stage Fresher Filtering Funnel.

Stage 1: Fast rule-based hard rejects (Title regex, exp > 2 yrs, senior phrases).
Stage 2: LLM classification for borderline jobs (batched 10 per call).
Stage 3: Fresher score (0-100) combining seniority fit, years fit, allow signals,
         candidate skill overlap, and posting freshness.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm import LLMProvider, get_llm_provider

logger = logging.getLogger(__name__)

# --- Stage 1 Patterns ---

REJECT_TITLE_TERMS = [
    r"\bsenior\b",
    r"\bsr\.?\b",
    r"\blead\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\bhead\s+of\b",
    r"\bdirector\b",
    r"\bvp\b",
    r"\bvice\s+president\b",
    r"\bmanager\b",
    r"\barchitect\b",
    r"\bdistinguished\b",
    r"\b(?:sde|engineer|developer|analyst)[ -]?(?:ii|iii|iv|v|2|3|4|5)\b",
    r"\bconsultant\b",
]

ALLOW_TITLE_TERMS = [
    r"\bintern\b",
    r"\binternship\b",
    r"\btrainee\b",
    r"\bgraduate\b",
    r"\bgraduate\s+engineer\s+trainee\b",
    r"\bget\b",
    r"\bentry[ -]?level\b",
    r"\bjunior\b",
    r"\bjr\.?\b",
    r"\bassociate\b",
    r"\bfresher\b",
    r"\b0-1\s*years?\b",
    r"\b0-2\s*years?\b",
    r"\b2025\b",
    r"\b2026\b",
    r"\bcampus\b",
    r"\bnew\s+grad\b",
    r"\bfresh\s+graduate\b",
]

REJECT_PHRASES_DESCRIPTION = [
    r"proven\s+track\s+record\s+of\s+leading\s+teams",
    r"mentor\s+junior\s+engineers",
    r"mentoring\s+junior",
    r"own\s+architecture",
    r"proven\s+leadership\s+experience",
    r"lead\s+a\s+team\s+of",
    r"proven\s+track\s+record\s+of\s+mentoring",
]

# Regex to detect years of experience
YEARS_EXP_PATTERNS = [
    re.compile(r"(\d+)\s*(?:\+)?\s*(?:-|to)\s*(\d+)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:relevant\s+|professional\s+|work\s+|hands-on\s+)?exp(?:erience)?)?", re.IGNORECASE),
    re.compile(r"(\d+)\s*\+\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:relevant\s+|professional\s+|work\s+|hands-on\s+)?exp(?:erience)?)?", re.IGNORECASE),
    re.compile(r"(?:minimum|at\s+least|requir(?:e|es|ed|ing))\s*(\d+)\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:relevant\s+|professional\s+|work\s+|hands-on\s+)?exp(?:erience)?)?", re.IGNORECASE),
]


def extract_years_of_experience(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extracts (min_years, max_years) required from text.
    Returns (None, None) if not explicitly mentioned.
    """
    if not text:
        return None, None

    lowest_min: Optional[int] = None
    matched_max: Optional[int] = None

    for pattern in YEARS_EXP_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            if len(groups) >= 2 and groups[1] is not None:
                min_yr = int(groups[0])
                max_yr = int(groups[1])
            else:
                min_yr = int(groups[0])
                max_yr = None

            if lowest_min is None or min_yr < lowest_min:
                lowest_min = min_yr
                matched_max = max_yr

    if lowest_min is not None:
        return lowest_min, matched_max

    # Fallback: check for explicit 0 experience phrases (e.g. no prior experience required, freshers welcome)
    if re.search(r"\b(no\s+(?:prior\s+)?experience\s+required|freshers?\s+welcome|college\s+graduates?)\b", text, re.IGNORECASE):
        return 0, 0

    return None, None


def check_stage1_rules(title: str, description: str) -> Dict[str, Any]:
    """
    Stage 1: Rule-based hard rejects.
    Returns dict:
      passed: bool
      reason: str
      min_years: Optional[int]
      max_years: Optional[int]
      has_allow_signal: bool
      is_obvious_fresher: bool
    """
    title_lower = title.lower() if title else ""
    desc_lower = description.lower() if description else ""

    # Check allow signals in title
    has_title_allow = any(re.search(pat, title_lower) for pat in ALLOW_TITLE_TERMS)
    has_desc_allow = any(re.search(pat, desc_lower) for pat in ALLOW_TITLE_TERMS)
    has_allow_signal = has_title_allow or has_desc_allow

    # Check reject terms in title
    has_title_reject = any(re.search(pat, title_lower) for pat in REJECT_TITLE_TERMS)
    if has_title_reject and not has_title_allow:
        return {
            "passed": False,
            "reason": f"Title '{title}' matches senior/leadership keyword reject rule.",
            "min_years": None,
            "max_years": None,
            "has_allow_signal": False,
            "is_obvious_fresher": False,
        }

    # Check reject phrases in description
    for phrase_pat in REJECT_PHRASES_DESCRIPTION:
        if re.search(phrase_pat, desc_lower):
            return {
                "passed": False,
                "reason": "Description requires leading teams or owning architecture.",
                "min_years": None,
                "max_years": None,
                "has_allow_signal": has_allow_signal,
                "is_obvious_fresher": False,
            }

    # Extract years of experience
    min_years, max_years = extract_years_of_experience(description)
    if min_years is not None and min_years > 2:
        return {
            "passed": False,
            "reason": f"Requires {min_years}+ years of experience (> 2 years limit).",
            "min_years": min_years,
            "max_years": max_years,
            "has_allow_signal": has_allow_signal,
            "is_obvious_fresher": False,
        }

    is_obvious_fresher = has_title_allow and (min_years is None or min_years <= 1)

    return {
        "passed": True,
        "reason": "Passed Stage 1 rules.",
        "min_years": min_years,
        "max_years": max_years,
        "has_allow_signal": has_allow_signal,
        "is_obvious_fresher": is_obvious_fresher,
    }


# --- Stage 2: LLM Classification ---

class JobClassificationItem(BaseModel):
    job_id: str
    seniority: str = Field(..., description="intern|entry|junior|mid|senior|lead")
    min_years_exp: Optional[int] = None
    fresher_friendly: bool
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    reason: str = Field(..., max_length=250)


class JobClassificationBatchResponse(BaseModel):
    classifications: List[JobClassificationItem]


def _load_prompt_template() -> str:
    prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "job_classification_v1.txt"
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    return (
        "You are an expert technical recruiter specializing in entry-level and fresher tech jobs (0-2 years).\n"
        "Return a JSON array of classifications for each job with seniority, min_years_exp, fresher_friendly, "
        "required_skills, nice_to_have_skills, reason."
    )


async def classify_jobs_with_llm(
    jobs: List[Dict[str, Any]],
    llm: Optional[LLMProvider] = None
) -> List[JobClassificationItem]:
    """
    Stage 2: Batches up to 10 borderline jobs to the LLM for strict classification.
    """
    if not jobs:
        return []

    if llm is None:
        llm = get_llm_provider()

    system_prompt = _load_prompt_template()

    # Prepare jobs payload (limit description to avoid Groq TPM limits)
    prepared = []
    for j in jobs:
        desc = j.get("description", "")
        # Truncate description intelligently to 1000 characters
        trimmed_desc = desc[:1000] if len(desc) > 1000 else desc
        prepared.append({
            "job_id": str(j.get("id", j.get("source_job_id", "unknown"))),
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "description": trimmed_desc,
        })

    user_prompt = f"Classify this batch of {len(prepared)} jobs:\n{json.dumps(prepared, indent=2)}"

    try:
        schema = JobClassificationBatchResponse.model_json_schema()
        result_json = await llm.complete_json(
            system=system_prompt,
            user=user_prompt,
            json_schema=schema,
            temperature=0.1,
        )
        batch = JobClassificationBatchResponse.model_validate(result_json)
        return batch.classifications
    except Exception as e:
        logger.warning("Stage 2 LLM classification failed: %s. Using heuristic fallback.", e)
        # Fallback to rule-based classification per job
        fallback_items = []
        for j in jobs:
            s1 = check_stage1_rules(j.get("title", ""), j.get("description", ""))
            fresher = s1["passed"] and (s1["min_years"] is None or s1["min_years"] <= 2)
            fallback_items.append(
                JobClassificationItem(
                    job_id=str(j.get("id", j.get("source_job_id", "unknown"))),
                    seniority="entry" if fresher else "mid",
                    min_years_exp=s1["min_years"] if s1["min_years"] is not None else 0,
                    fresher_friendly=fresher,
                    required_skills=[],
                    nice_to_have_skills=[],
                    reason="Heuristic fallback: " + s1["reason"]
                )
            )
        return fallback_items


# --- Stage 3: Fresher Score Calculation ---

def normalize_skill(s: str) -> str:
    """Normalize a skill token for matching."""
    if not s:
        return ""
    cleaned = s.lower().strip()
    cleaned = re.sub(r"\b(js|\.js|framework|library|technologies|tools)\b", "", cleaned).strip()
    return re.sub(r"[^a-z0-9+#]", "", cleaned)


def compute_fresher_score(
    seniority: str,
    min_years: Optional[int],
    title: str,
    description: str,
    posted_at: Optional[datetime] = None,
    candidate_skills: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
    nice_to_have_skills: Optional[List[str]] = None,
) -> Tuple[int, int, List[str], List[str], str]:
    """
    Stage 3: Calculates fresher_score (0-100) and match metrics.
    Returns:
      (fresher_score, match_percent, matched_skills, missing_skills, fit_reason)
    """
    score = 0
    reasons = []

    # 1. Seniority fit (0 - 40 points)
    sen = (seniority or "entry").lower()
    if sen == "intern":
        score += 40
        reasons.append("Internship role suited for freshers (+40)")
    elif sen == "entry":
        score += 40
        reasons.append("Entry-level role (+40)")
    elif sen == "junior":
        score += 35
        reasons.append("Junior role (+35)")
    elif sen == "mid":
        score += 10
        reasons.append("Mid-level role (+10)")
    else:  # senior/lead
        score += 0

    # 2. Years fit (0 - 25 points)
    if min_years is not None:
        if min_years <= 1:
            score += 25
            reasons.append(f"{min_years} yr experience requirement (+25)")
        elif min_years <= 2:
            score += 20
            reasons.append(f"{min_years} yrs experience requirement (+20)")
        else:
            score += 0
    else:
        score += 15
        reasons.append("Unspecified experience requirements (+15)")

    # 3. Title allow-signals (+10 points)
    title_lower = title.lower() if title else ""
    if any(re.search(pat, title_lower) for pat in ALLOW_TITLE_TERMS):
        score += 10
        reasons.append("Title explicitly targets freshers/graduates (+10)")

    # 4. Skill overlap (0 - 20 points)
    matched: List[str] = []
    missing: List[str] = []
    match_percent = 50  # default when no candidate skills provided

    req_set = {normalize_skill(s) for s in (required_skills or []) if normalize_skill(s)}
    nice_set = {normalize_skill(s) for s in (nice_to_have_skills or []) if normalize_skill(s)}

    # If job didn't have explicit extracted skills, derive some basic ones from text
    if not req_set and not nice_set:
        common_tech = ["python", "javascript", "react", "node", "sql", "java", "c++", "aws", "docker", "git", "html", "css", "fastapi", "django"]
        job_body = f"{title} {description}".lower()
        req_set = {tech for tech in common_tech if tech in job_body}

    if candidate_skills:
        cand_norm = {normalize_skill(s): s for s in candidate_skills if normalize_skill(s)}
        cand_keys = set(cand_norm.keys())

        matched_req = req_set.intersection(cand_keys)
        missing_req = req_set.difference(cand_keys)
        matched_nice = nice_set.intersection(cand_keys)

        total_weight = (len(req_set) * 2) + len(nice_set)
        earned_weight = (len(matched_req) * 2) + len(matched_nice)

        if total_weight > 0:
            skill_fraction = earned_weight / total_weight
            skill_points = int(round(skill_fraction * 20))
            match_percent = int(round(skill_fraction * 100))
        else:
            skill_points = 12
            match_percent = 60

        score += skill_points
        matched = [cand_norm[k] for k in (matched_req | matched_nice) if k in cand_norm]
        missing = list(missing_req)
        if matched:
            reasons.append(f"{len(matched)} skills matched (+{skill_points})")
    else:
        # Default skill score if candidate profile has no skills listed
        score += 12
        match_percent = 60

    # 5. Freshness (0 - 5 points)
    if posted_at:
        now = datetime.now(timezone.utc)
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (now - posted_at).total_seconds() / 3600.0
        if age_hours <= 48:
            score += 5
            reasons.append("Posted within 48 hours (+5)")
        elif age_hours <= 168:  # 7 days
            score += 3
            reasons.append("Posted within 7 days (+3)")
        elif age_hours <= 336:  # 14 days
            score += 1
            reasons.append("Posted within 14 days (+1)")

    fresher_score = max(0, min(100, score))
    fit_reason = "; ".join(reasons[:3]) if reasons else "Fresher-appropriate role."

    return fresher_score, match_percent, matched, missing, fit_reason
