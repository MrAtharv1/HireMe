"""
Canonical Facts Store for Candidates (Step 1).
Single Source of Truth:
- Candidate's CV is immutable.
- Precomputes deterministically for each bullet and item:
  * tools_mentioned (via taxonomy and synonym mapping)
  * numbers_present (digits, percentages, metrics, currency)
  * proper_nouns
  * dates_present
- Provides versioned implication mapping (implications.yaml)
- Supports user-edited facts store updates before tailoring.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

TAXONOMY_DIR = Path(__file__).resolve().parent / "taxonomy"


def load_implications() -> Dict[str, List[str]]:
    """Loads versioned implications mapping."""
    imp_file = TAXONOMY_DIR / "implications.yaml"
    if imp_file.is_file():
        try:
            with open(imp_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("implications", {})
        except Exception as e:
            logger.warning("Failed to load implications.yaml: %s", e)
    return {
        "fastapi": ["Python", "REST APIs", "RESTful APIs", "Backend", "APIs"],
        "react": ["JavaScript", "Frontend", "UI", "Web Development"],
        "postgresql": ["SQL", "Relational Databases", "Databases"],
        "docker": ["Containerization", "DevOps"],
        "pytest": ["Unit Testing", "Testing", "Python"],
    }


def load_synonyms() -> Dict[str, str]:
    """Loads versioned synonym mapping for term alignment."""
    syn_file = TAXONOMY_DIR / "synonyms.yaml"
    if syn_file.is_file():
        try:
            with open(syn_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("synonyms", {})
        except Exception as e:
            logger.warning("Failed to load synonyms.yaml: %s", e)
    return {
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "py": "Python",
        "python": "Python",
        "rest": "REST APIs",
        "restful": "RESTful APIs",
        "rest apis": "REST APIs",
        "restful apis": "RESTful APIs",
        "ml": "Machine Learning",
        "k8s": "Kubernetes",
        "react": "React",
        "reactjs": "React",
        "node": "Node.js",
        "nodejs": "Node.js",
        "golang": "Go",
        "go": "Go",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "dsa": "Data Structures & Algorithms",
    }


IMPLICATIONS_MAP = load_implications()
SYNONYMS_MAP = load_synonyms()


def normalize_skill_token(token: str) -> str:
    """Normalize skill token to lowercase alphanumeric for reliable matching."""
    if not token:
        return ""
    cleaned = token.lower().strip()
    cleaned = re.sub(r"\b(framework|library|tools|technologies)\b", "", cleaned).strip()
    return re.sub(r"[^a-z0-9+#]", "", cleaned)


def resolve_canonical_skill_name(raw_name: str) -> str:
    """Maps raw skill token through synonym dictionary."""
    if not raw_name:
        return ""
    norm = raw_name.lower().strip()
    if norm in SYNONYMS_MAP:
        return SYNONYMS_MAP[norm]
    return raw_name.strip()


def extract_numbers_tokens(text: str) -> List[str]:
    """
    Extracts all numeric, percentage, and currency metrics present in text.
    Examples: '12', '28%', '$500', '3.8', '100+'
    """
    if not text:
        return []
    matches = re.findall(r"[$€£₹]?\s*\d+(?:[.,]\d+)?(?:%|x|k|m|\+)?", text, re.IGNORECASE)
    cleaned = []
    for m in matches:
        m_str = m.strip().lower()
        if m_str and m_str not in cleaned:
            cleaned.append(m_str)
    return cleaned


def extract_dates_tokens(text: str) -> List[str]:
    """Extracts date and year tokens from text."""
    if not text:
        return []
    pattern = (
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
        r"\d{4})\b"
    )
    matches = re.findall(pattern, text, re.IGNORECASE)
    return sorted(list({m.lower() for m in matches}))


def extract_proper_nouns_tokens(text: str) -> List[str]:
    """
    Extracts capitalized proper nouns (companies, entities, specialized names) from text.
    """
    if not text:
        return []
    # Find words starting with capital letters, excluding simple sentence starts
    words = text.split()
    proper = []
    for i, w in enumerate(words):
        w_clean = re.sub(r"[^\w+#]", "", w)
        if w_clean and w_clean[0].isupper() and len(w_clean) > 1:
            # Exclude standard common starters if first word
            if i == 0 and w_clean.lower() in {"engineered", "developed", "built", "implemented", "created", "designed"}:
                continue
            if w_clean not in proper:
                proper.append(w_clean)
    return proper


GLOBAL_TECH_TAXONOMY: Set[str] = {
    "python", "javascript", "typescript", "java", "c++", "c", "golang", "go", "rust",
    "c#", ".net", "ruby", "php", "swift", "kotlin", "sql", "r", "html", "css",
    "react", "angular", "vue", "next.js", "nextjs", "node", "nodejs", "node.js",
    "express", "fastapi", "django", "flask", "spring", "spring boot",
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "cassandra",
    "elasticsearch", "dynamodb", "firebase", "supabase", "mariadb",
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform", "jenkins",
    "git", "github", "gitlab", "ci/cd", "cicd", "graphql", "rest", "rest apis",
    "restful apis", "kafka", "rabbitmq", "linux", "postman", "selenium", "cypress",
    "pandas", "numpy", "pytorch", "tensorflow", "keras", "scikit-learn", "pytest"
}


def extract_tools_from_text(text: str, candidate_skills: Optional[List[str]] = None) -> List[str]:
    """
    Identify all technical tools mentioned in text against candidate skills,
    synonym mappings, and the global technical taxonomy.
    """
    if not text:
        return []
    text_lower = text.lower()
    found: List[str] = []

    # 1. Match against candidate's known skills
    if candidate_skills:
        for skill in candidate_skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                canon = resolve_canonical_skill_name(skill)
                if canon not in found:
                    found.append(canon)

    # 2. Match against known synonyms map
    for syn_key, syn_val in SYNONYMS_MAP.items():
        if re.search(r"\b" + re.escape(syn_key) + r"\b", text_lower):
            if syn_val not in found:
                found.append(syn_val)

    # 3. Match against global technology taxonomy
    for tech in GLOBAL_TECH_TAXONOMY:
        if re.search(r"\b" + re.escape(tech) + r"\b", text_lower):
            canon = resolve_canonical_skill_name(tech)
            if canon not in found:
                found.append(canon)

    return found


def get_implied_skills_for_tool(tool_name: str) -> List[str]:
    """Returns direct implications for a given tool from implications.yaml."""
    norm = normalize_skill_token(tool_name)
    results = []
    for k, v in IMPLICATIONS_MAP.items():
        if normalize_skill_token(k) == norm:
            results.extend(v)
    return results


class FactBullet(BaseModel):
    """
    Immutable fact record for a single resume bullet point.
    Precomputes evidence tokens for deterministic verifier checks.
    """
    id: str
    section: str = "experience"
    item_index: int = 0
    bullet_index: int = 0
    entity: str = ""
    role_or_degree: str = ""
    dates: str = ""
    original_text: str = ""
    tools_mentioned: List[str] = Field(default_factory=list)
    numbers_present: List[str] = Field(default_factory=list)
    proper_nouns: List[str] = Field(default_factory=list)
    dates_present: List[str] = Field(default_factory=list)


class CanonicalFactsStore(BaseModel):
    """
    Container of candidate's canonical ground-truth data.
    The single source of truth for all resume tailoring.
    """
    user_id: Optional[str] = None
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

    canonical_skills: List[str] = Field(default_factory=list)
    normalized_skills: Set[str] = Field(default_factory=set)

    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

    bullets: Dict[str, FactBullet] = Field(default_factory=dict)
    experience_entries: List[Dict[str, Any]] = Field(default_factory=list)
    project_entries: List[Dict[str, Any]] = Field(default_factory=list)

    def get_all_numbers(self) -> Set[str]:
        """Aggregate all numbers and metrics in the entire facts store."""
        nums = set()
        for b in self.bullets.values():
            nums.update(b.numbers_present)
        return nums

    def get_all_tools(self) -> Set[str]:
        """Aggregate all tools mentioned anywhere in facts or canonical skills."""
        tools = set(self.canonical_skills)
        for b in self.bullets.values():
            tools.update(b.tools_mentioned)
        return tools

    def get_implied_skills(self) -> Set[str]:
        """Returns all skills implied by any tool in candidate's facts."""
        implied = set()
        for t in self.get_all_tools():
            implied.update(get_implied_skills_for_tool(t))
        return implied


def build_canonical_facts(profile_json: Dict[str, Any]) -> CanonicalFactsStore:
    """
    Constructs an immutable CanonicalFactsStore from raw parsed_json.
    Assigns stable bullet IDs and builds ground-truth skill inventory and evidence tokens.
    """
    personal = profile_json.get("personal_info") or profile_json.get("personal") or {}
    contact = profile_json.get("contact") or {}

    name = personal.get("name") or contact.get("name") or profile_json.get("name") or ""
    email = personal.get("email") or contact.get("email") or profile_json.get("email") or ""
    phone = personal.get("phone") or contact.get("phone") or profile_json.get("phone") or ""
    location = personal.get("location") or contact.get("location") or profile_json.get("location") or ""
    linkedin = personal.get("linkedin") or contact.get("linkedin") or profile_json.get("linkedin") or ""
    github = personal.get("github") or contact.get("github") or profile_json.get("github") or ""
    portfolio = (
        personal.get("portfolio")
        or contact.get("portfolio")
        or personal.get("website")
        or profile_json.get("portfolio")
        or ""
    )

    raw_skills = profile_json.get("skills") or []
    if isinstance(raw_skills, dict):
        all_skills = []
        for v in raw_skills.values():
            if isinstance(v, list):
                all_skills.extend(v)
        raw_skills = all_skills

    # Collect project tools as well
    proj_entries = profile_json.get("projects") or []
    for proj in proj_entries:
        p_tools = proj.get("technologies") or proj.get("tools") or []
        if isinstance(p_tools, list):
            raw_skills.extend(p_tools)
        elif isinstance(p_tools, str):
            raw_skills.extend([t.strip() for t in p_tools.split(",") if t.strip()])

    # Deduplicate and resolve synonyms
    canonical_skills: List[str] = []
    normalized_skills: Set[str] = set()
    for s in raw_skills:
        if isinstance(s, str) and s.strip():
            canon = resolve_canonical_skill_name(s.strip())
            if canon not in canonical_skills:
                canonical_skills.append(canon)
                normalized_skills.add(normalize_skill_token(canon))

    canonical_skills.sort()
    bullets_dict: Dict[str, FactBullet] = {}

    # 1. Process Experience entries
    exp_entries = profile_json.get("experience") or []
    for i, exp in enumerate(exp_entries):
        company = exp.get("company", "Company")
        role = exp.get("role") or exp.get("title", "Software Engineer")
        dates = exp.get("dates") or f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}".strip(" -")
        exp_bullets = exp.get("bullets") or exp.get("bullet_points") or exp.get("description") or []
        if isinstance(exp_bullets, str):
            exp_bullets = [b.strip() for b in exp_bullets.split("\n") if b.strip()]

        for j, b_text in enumerate(exp_bullets):
            b_id = f"exp_{i}_b{j}"
            techs = extract_tools_from_text(b_text, canonical_skills)
            nums = extract_numbers_tokens(b_text)
            nouns = extract_proper_nouns_tokens(b_text)
            d_tokens = extract_dates_tokens(b_text)

            bullets_dict[b_id] = FactBullet(
                id=b_id,
                section="experience",
                item_index=i,
                bullet_index=j,
                entity=company,
                role_or_degree=role,
                dates=dates,
                original_text=b_text,
                tools_mentioned=techs,
                numbers_present=nums,
                proper_nouns=nouns,
                dates_present=d_tokens,
            )

    # 2. Process Projects entries
    for i, proj in enumerate(proj_entries):
        p_name = proj.get("name") or proj.get("title", f"Project {i+1}")
        dates = proj.get("dates") or proj.get("date", "")
        p_bullets = proj.get("bullets") or proj.get("bullet_points") or proj.get("description") or []
        if isinstance(p_bullets, str):
            p_bullets = [b.strip() for b in p_bullets.split("\n") if b.strip()]

        for j, b_text in enumerate(p_bullets):
            b_id = f"proj_{i}_b{j}"
            techs = extract_tools_from_text(b_text, canonical_skills)
            # Add tools listed in project header to this bullet's tool scope if relevant
            p_tools = proj.get("technologies") or proj.get("tools") or []
            if isinstance(p_tools, list):
                for pt in p_tools:
                    c_pt = resolve_canonical_skill_name(pt)
                    if c_pt and c_pt not in techs and c_pt.lower() in b_text.lower():
                        techs.append(c_pt)

            nums = extract_numbers_tokens(b_text)
            nouns = extract_proper_nouns_tokens(b_text)
            d_tokens = extract_dates_tokens(b_text)

            bullets_dict[b_id] = FactBullet(
                id=b_id,
                section="projects",
                item_index=i,
                bullet_index=j,
                entity=p_name,
                role_or_degree="Developer",
                dates=dates,
                original_text=b_text,
                tools_mentioned=techs,
                numbers_present=nums,
                proper_nouns=nouns,
                dates_present=d_tokens,
            )

    certifications = profile_json.get("certifications") or []
    achievements = profile_json.get("achievements") or []

    for item in certifications + achievements:
        if isinstance(item, str):
            for word in re.findall(r"\b[A-Za-z0-9+#.-]{2,20}\b", item):
                canon = resolve_canonical_skill_name(word)
                if canon:
                    normalized_skills.add(normalize_skill_token(canon))

    return CanonicalFactsStore(
        name=name,
        email=email,
        phone=phone,
        location=location,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
        canonical_skills=canonical_skills,
        normalized_skills=normalized_skills,
        education=profile_json.get("education") or [],
        certifications=certifications,
        achievements=achievements,
        bullets=bullets_dict,
        experience_entries=exp_entries,
        project_entries=proj_entries,
    )
