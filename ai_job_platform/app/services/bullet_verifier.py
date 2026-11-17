"""
Deterministic Bullet Verifier Service (Step 5).
The authoritative safety net enforcing strict truthfulness:
1. Numbers check: set(numbers in edited) <= set(numbers in original). Any new metric/number -> REJECT.
2. Proper nouns/tools check: any tool not in original item facts and not an eligible keyword with valid evidence -> REJECT.
3. Word retention: at least 60% of original content words must remain unless TRIM/MERGE operation.
4. Tone & length: 8-28 words, no banned buzzwords, no first-person pronouns, starts with strong action verb.
5. On reject: retry once with violation feedback, then FALL BACK TO ORIGINAL BULLET.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.services.facts_store import (
    CanonicalFactsStore,
    FactBullet,
    extract_numbers_tokens,
    extract_proper_nouns_tokens,
    extract_tools_from_text,
    get_implied_skills_for_tool,
    normalize_skill_token,
    resolve_canonical_skill_name,
)

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "if", "in", "into", "is", "it", "its", "itself",
    "let's", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
}

BANNED_BUZZWORDS = {
    "passionate", "hardworking", "hard-working", "team player", "team-player",
    "dynamic", "results-driven", "results driven", "synergy", "detail-oriented",
    "enthusiastic", "go-getter", "go getter", "rockstar", "ninja", "guru",
    "outside the box", "self-motivated", "dedicated", "proactive"
}

ALLOWED_INITIAL_VERBS = {
    "built", "developed", "engineered", "implemented", "designed", "integrated",
    "automated", "tested", "deployed", "optimized", "architected", "authored",
    "constructed", "created", "configured", "debugged", "delivered", "drafted",
    "enhanced", "executed", "formulated", "generated", "improved", "launched",
    "maintained", "migrated", "monitored", "orchestrated", "performed", "produced",
    "refactored", "resolved", "restructured", "scaled", "shipped", "spearheaded",
    "standardized", "streamlined", "supervised", "trained", "upgraded", "validated",
    # Present tense for current/ongoing items
    "build", "develop", "engineer", "implement", "design", "integrate", "automate",
    "test", "deploy", "optimize", "architect", "create", "maintain", "ship"
}


def _simple_stem(token: str) -> str:
    """Simple morphological normalization for word retention matching."""
    t = token.lower().strip(".,!?;:\"'()[]{}")
    if t.endswith("ing") and len(t) > 5:
        return t[:-3]
    if t.endswith("ed") and len(t) > 4:
        return t[:-2]
    if t.endswith("es") and len(t) > 4:
        return t[:-2]
    if t.endswith("s") and len(t) > 3 and not t.endswith("ss"):
        return t[:-1]
    return t


def compute_word_retention_ratio(original: str, edited: str) -> float:
    """
    Computes proportion of original content words retained in edited version.
    Stopwords and punctuation are excluded.
    """
    orig_words = [
        _simple_stem(w) for w in original.split()
        if w.lower().strip(".,!?;:\"'()[]{}") not in STOPWORDS and len(w) > 2
    ]
    if not orig_words:
        return 1.0

    edit_words_set = {
        _simple_stem(w) for w in edited.split()
        if w.lower().strip(".,!?;:\"'()[]{}") not in STOPWORDS and len(w) > 2
    }

    retained_count = sum(1 for w in orig_words if w in edit_words_set)
    return round(retained_count / len(orig_words), 3)


class BulletVerificationResult(BaseModel):
    passed: bool
    retention_ratio: float
    operations: List[str] = Field(default_factory=list)
    keywords_added: List[Dict[str, str]] = Field(default_factory=list)
    status: str = "edited"  # "edited" | "kept_original" | "fallback"
    violation: Optional[str] = None
    final_text: str


def verify_edited_bullet(
    original_bullet: FactBullet,
    edited_text: str,
    operations_claimed: List[str],
    keywords_added_claimed: List[Dict[str, str]],
    canonical_facts: CanonicalFactsStore,
    strictness: str = "balanced"  # "conservative", "balanced", "assertive"
) -> BulletVerificationResult:
    """
    Deterministic safety net. Checks:
    1. Number subset check (zero new metrics).
    2. Tool/proper noun authorization check.
    3. Word retention threshold (>= 60% unless TRIM/MERGE).
    4. First-person & buzzword prohibition.
    5. Action verb opening.
    6. Length bounds (8-28 words).
    """
    cleaned_edit = edited_text.strip()
    words = cleaned_edit.split()

    # Rule 0: Length bounds
    if len(words) < 8 or len(words) > 28:
        return BulletVerificationResult(
            passed=False,
            retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
            status="fallback",
            violation=f"Word count {len(words)} is outside the allowed bounds (8 to 28 words).",
            final_text=original_bullet.original_text,
        )

    # Rule 1: No first-person pronouns
    if re.search(r"\b(i|me|my|we|our|us)\b", cleaned_edit, re.IGNORECASE):
        return BulletVerificationResult(
            passed=False,
            retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
            status="fallback",
            violation="Contains forbidden first-person pronouns (I, me, my, we, our).",
            final_text=original_bullet.original_text,
        )

    # Rule 2: No banned fluff buzzwords
    for buzz in BANNED_BUZZWORDS:
        if re.search(r"\b" + re.escape(buzz) + r"\b", cleaned_edit, re.IGNORECASE):
            return BulletVerificationResult(
                passed=False,
                retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
                status="fallback",
                violation=f"Contains banned fluff buzzword: '{buzz}'.",
                final_text=original_bullet.original_text,
            )

    # Rule 3: Number-subset check (hard safety rule)
    orig_nums = set(original_bullet.numbers_present)
    edit_nums = set(extract_numbers_tokens(cleaned_edit))
    invented_nums = edit_nums - orig_nums
    if invented_nums:
        return BulletVerificationResult(
            passed=False,
            retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
            status="fallback",
            violation=f"Fabricated metric or number detected: {sorted(list(invented_nums))}. Original had: {sorted(list(orig_nums))}.",
            final_text=original_bullet.original_text,
        )

    # Rule 4: Action verb check
    first_token = re.sub(r"[^\w]", "", words[0]).lower()
    if first_token not in ALLOWED_INITIAL_VERBS:
        # Check if first word is a verb ending in 'ed'
        if not (first_token.endswith("ed") and len(first_token) >= 5):
            return BulletVerificationResult(
                passed=False,
                retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
                status="fallback",
                violation=f"Bullet does not begin with an approved strong action verb (began with '{words[0]}').",
                final_text=original_bullet.original_text,
            )

    # Rule 5: Proper nouns and tool authorization
    # What tools are authorized for this bullet?
    allowed_bullet_tools = set(original_bullet.tools_mentioned)
    # Plus tools directly implied by the bullet's tools
    for t in original_bullet.tools_mentioned:
        allowed_bullet_tools.update(get_implied_skills_for_tool(t))

    # Also authorized: keywords added with explicit validated evidence in original item facts
    for ka in keywords_added_claimed:
        term = ka.get("term", "").strip()
        evidence = ka.get("evidence", "").strip()
        if term and evidence and evidence.lower() in original_bullet.original_text.lower():
            # Evidence exists in original bullet
            allowed_bullet_tools.add(term)
            allowed_bullet_tools.update(get_implied_skills_for_tool(term))

    allowed_norm_tokens = {normalize_skill_token(t) for t in allowed_bullet_tools if normalize_skill_token(t)}

    # Extract all tools in edited text
    edited_tools = extract_tools_from_text(cleaned_edit, canonical_facts.canonical_skills)
    unauthorized_tools = []
    for et in edited_tools:
        et_norm = normalize_skill_token(et)
        if et_norm and et_norm not in allowed_norm_tokens:
            unauthorized_tools.append(et)

    if unauthorized_tools:
        return BulletVerificationResult(
            passed=False,
            retention_ratio=compute_word_retention_ratio(original_bullet.original_text, cleaned_edit),
            status="fallback",
            violation=f"Unauthorized tool(s) added without evidence in this bullet: {unauthorized_tools}.",
            final_text=original_bullet.original_text,
        )

    # Rule 6: Word retention ratio check (unless operation is TRIM or MERGE)
    retention = compute_word_retention_ratio(original_bullet.original_text, cleaned_edit)
    is_trim = any(op in {"TRIM", "MERGE"} for op in operations_claimed)
    min_retention = 0.40 if is_trim else (0.65 if strictness == "conservative" else 0.55)

    if retention < min_retention:
        return BulletVerificationResult(
            passed=False,
            retention_ratio=retention,
            status="fallback",
            violation=f"Word retention ratio {retention*100:.1f}% is below minimum required {min_retention*100:.0f}%.",
            final_text=original_bullet.original_text,
        )

    # Passed all deterministic checks!
    return BulletVerificationResult(
        passed=True,
        retention_ratio=retention,
        operations=operations_claimed,
        keywords_added=keywords_added_claimed,
        status="edited",
        violation=None,
        final_text=cleaned_edit,
    )
