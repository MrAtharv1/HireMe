"""
Hybrid Recommendation Engine MVP.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.models.db_models import Job


def _extract_keywords(text: str) -> set:
    """Simple keyword extractor converting text to lowercase word set."""
    if not text:
        return set()
    words = re.findall(r'\b[a-z0-9+#-]+\b', text.lower())
    return set(words)


def normalize_skill(s: str) -> str:
    """Standardises skills (e.g., 'React js' -> 'react')"""
    return s.lower().replace("js", "").replace(".js", "").strip()


def calculate_match_score(profile_json: Dict[str, Any], job: Job) -> Tuple[int, List[str]]:
    """
    Calculate a match score (0-100) and generate reasoning.
    """
    score = 0
    reasons = []
    
    job_text = f"{job.title} {job.description}".lower()
    
    # 1. Smarter Skill Match (Max 40 points)
    skills = profile_json.get("skills", [])
    if skills:
        matched_skills = []
        for s in skills:
            norm_s = normalize_skill(s)
            if norm_s and norm_s in job_text:
                matched_skills.append(s)
                
        skill_score = min(40, len(matched_skills) * 5)
        score += skill_score
        if skill_score > 20:
            reasons.append(f"Strong skill overlap ({len(matched_skills)} matched: {', '.join(matched_skills[:3])}...)")
        elif skill_score > 0:
            reasons.append("Partial skill match.")

    # 2. Role Relevance (Max 25 points)
    exp_titles = [exp.get("title", "").lower() for exp in profile_json.get("experience", []) if exp.get("title")]
    title_words = _extract_keywords(job.title)
    
    role_match_found = False
    for et in exp_titles:
        if any(w in et for w in title_words if len(w) > 3):
            role_match_found = True
            break
            
    if role_match_found:
        score += 25
        reasons.append("Highly relevant to past experience.")

    # 3. Fresher/Experience Fit (Max 20 points)
    desc_lower = job.description.lower()
    if any(kw in job.title.lower() for kw in ["junior", "intern", "entry", "graduate", "trainee"]) or \
       any(kw in desc_lower for kw in ["0-1", "entry level", "graduate"]):
        score += 20
        reasons.append("Great fit for freshers/juniors.")
    
    # 4. Job Freshness (Max 15 points)
    if job.created_at:
        now = datetime.now(timezone.utc) if job.created_at.tzinfo else datetime.utcnow()
        days_old = (now - job.created_at).days
        if days_old <= 3:
            score += 15
            reasons.append("Very recently posted.")
        elif days_old <= 14:
            score += 5

    # 5. Strategic Callback Boost (Max +15 bonus points)
    high_callback_keywords = ["qa", "support", "analyst", "trainee", "quality assurance", "helpdesk"]
    job_title_lower = job.title.lower()
    job_category = getattr(job, "category", "")

    if any(kw in job_title_lower for kw in high_callback_keywords) or job_category in ["qa", "customer-support", "data"]:
        score += 15
        reasons.append("High-callback probability role category.")
            
    return min(100, score), reasons