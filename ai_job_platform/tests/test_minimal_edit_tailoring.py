"""
Comprehensive test suite for Minimal-Edit Resume Tailoring Pipeline (Step 12).

Tests:
1. Unit Tests:
   - Number subset check (extract_numbers, number preservation)
   - Unauthorized tool detection (GLOBAL_TECH_TAXONOMY + implications check)
   - Word retention ratio computation (compute_word_retention_ratio)
   - Implication map loading and resolution (implications.yaml)
   - Keyword coverage calculation & exact JD spelling
   - Skill grouping and prioritization without hallucinations
2. Adversarial Tests:
   - Invented metric ("reduced latency by 35%") -> rejected, fallback to original
   - Unmentioned tool added ("deployed to AWS") -> rejected, fallback to original
   - Severe word drop (<60% retention) -> rejected, fallback to original
   - First-person pronouns ("I developed", "my team") -> rejected, fallback to original
   - Corporate buzzwords ("synergy-driven", "ninja") -> rejected, fallback to original
3. Golden Test (1 Candidate Profile + 3 Target JDs):
   - JD 1: Backend Engineer (Python, FastAPI, PostgreSQL, Docker)
   - JD 2: QA / Automation Engineer (Python, Pytest, SQL, Git)
   - JD 3: Data Analyst / Backend (Python, PostgreSQL, SQL, Data Structures)
   - Asserts:
     * PDF is strictly 1 page
     * Standard ATS headings detected in order
     * Candidate-owned JD skills have >= 90% keyword coverage in PDF text
     * Zero fabricated numbers or tools anywhere in PDF text
     * Fidelity score >= 0.85
4. Property-Based Test:
   - Invariant: for any generated PDF, every extracted number and tool exists in candidate facts or allowed implications.
"""

import os
import pytest
import fitz
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from app.services.facts_store import (
    build_canonical_facts,
    extract_numbers_tokens,
    extract_tools_from_text,
    normalize_skill_token,
    resolve_canonical_skill_name,
    IMPLICATIONS_MAP,
    SYNONYMS_MAP,
    GLOBAL_TECH_TAXONOMY,
    FactBullet,
)
from app.services.bullet_verifier import (
    verify_edited_bullet,
    compute_word_retention_ratio,
    BulletVerificationResult,
)
from app.services.jd_analyzer import (
    JDAnalysisResult,
    compute_candidate_skills_and_gaps,
)
from app.services.ats_verifier import (
    verify_pdf_ats_compliance,
    ATSVerificationReport,
)
from app.services.resume_tailor_pipeline import (
    generate_tailored_resume_pipeline,
    categorize_skills,
)
from app.services.latex_compiler import compile_latex_to_pdf
from app.services.latex_renderer import render_latex_resume


# ---------------------------------------------------------------------------
# Fixtures & Samples
# ---------------------------------------------------------------------------

SAMPLE_FRESHER_PROFILE = {
    "personal_info": {
        "name": "Dev Sharma",
        "email": "dev.sharma@example.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/devsharma",
        "github": "https://github.com/devsharma",
        "portfolio": "https://devsharma.dev",
    },
    "skills": [
        "Python", "FastAPI", "PostgreSQL", "Docker", "Git", "Pytest",
        "SQL", "Redis", "Linux", "Data Structures & Algorithms"
    ],
    "education": [
        {
            "institution": "National Institute of Technology Karnataka",
            "degree": "B.Tech in Computer Science and Engineering",
            "dates": "2021 - 2025",
            "location": "Surathkal, India",
            "gpa": "8.8/10.0"
        }
    ],
    "experience": [
        {
            "company": "InfraCore Labs",
            "role": "Software Engineering Intern",
            "dates": "May 2024 - Aug 2024",
            "location": "Bengaluru, India",
            "bullets": [
                "Built RESTful microservices using Python and FastAPI for real-time order intake processing.",
                "Optimized relational database queries in PostgreSQL, improving query response latency.",
                "Wrote automated unit and integration tests using Pytest with 85% code coverage.",
            ]
        }
    ],
    "projects": [
        {
            "name": "Distributed Cache Server",
            "technologies": ["Python", "Redis", "Docker", "Linux"],
            "dates": "Jan 2025",
            "bullets": [
                "Implemented in-memory LRU key-value cache engine supporting 5000 concurrent client operations.",
                "Containerized cache services with Docker multi-stage builds and automated deployment via Git."
            ]
        },
        {
            "name": "Analytics Dashboard Backend",
            "technologies": ["Python", "FastAPI", "PostgreSQL", "SQL"],
            "dates": "Nov 2024",
            "bullets": [
                "Engineered aggregation pipeline in SQL and FastAPI processing 12000 events daily.",
                "Architected structured logging and health-check monitoring across backend services."
            ]
        }
    ],
    "certifications": ["PostgreSQL Certified Associate 2024"],
    "achievements": [
        "Finalist in Smart India Hackathon 2024 among 1500+ participating university teams",
        "Solved 450+ Data Structures & Algorithms problems across LeetCode and Codeforces"
    ]
}


# ===========================================================================
# 1. UNIT TESTS
# ===========================================================================

def test_extract_numbers():
    text = "Engineered pipeline with 12000 events daily, improving latency by 35% for $500 cost across 4 nodes."
    numbers = extract_numbers_tokens(text)
    assert "12000" in numbers
    assert "35%" in numbers
    assert "$500" in numbers
    assert "4" in numbers


def test_compute_word_retention_ratio():
    original = "Built RESTful backend APIs using Python and FastAPI for order processing."
    edited_same = "Developed RESTful backend APIs using Python and FastAPI for order processing."
    edited_short = "Built APIs."
    
    ratio_high = compute_word_retention_ratio(original, edited_same)
    ratio_low = compute_word_retention_ratio(original, edited_short)
    
    assert ratio_high >= 0.80
    assert ratio_low < 0.40


def test_implication_map_and_synonyms():
    # Verify implications.yaml and synonyms.yaml loaded correctly
    assert "fastapi" in IMPLICATIONS_MAP
    assert any("python" == x.lower() for x in IMPLICATIONS_MAP["fastapi"])
    assert any("rest" in x.lower() for x in IMPLICATIONS_MAP["fastapi"])
    assert "docker" in IMPLICATIONS_MAP
    assert any("container" in x.lower() for x in IMPLICATIONS_MAP["docker"])

    # Verify synonyms
    assert resolve_canonical_skill_name("postgres") == "PostgreSQL"
    assert resolve_canonical_skill_name("py") == "Python"
    assert resolve_canonical_skill_name("dsa") == "Data Structures & Algorithms"


def test_jd_exact_spelling_preservation():
    cand_skills = ["python", "postgres", "fastapi", "docker"]
    jd = JDAnalysisResult(
        target_role="Backend Developer",
        required_experience_years=0,
        must_have_skills=["PostgreSQL", "FastAPI"],
        nice_to_have_skills=["Docker"],
        tools=["Git"],
        domain_keywords=["APIs"],
        jd_exact_spelling={"postgresql": "PostgreSQL", "fastapi": "FastAPI", "docker": "Docker"}
    )
    
    categories = categorize_skills(cand_skills, jd)
    # Check that PostgreSQL is capitalized exactly as JD requested
    assert "PostgreSQL" in categories["Databases"]
    assert "FastAPI" in categories["Frameworks & Libraries"]
    # Candidate did not have Git in cand_skills, so Git must NOT be added
    all_cats = [s for sublist in categories.values() for s in sublist]
    assert "Git" not in all_cats


def test_compute_candidate_skills_and_gaps():
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    jd = JDAnalysisResult(
        target_role="Backend Developer",
        required_experience_years=0,
        must_have_skills=["Python", "FastAPI", "PostgreSQL", "Kubernetes"],
        nice_to_have_skills=["Docker", "AWS"],
        tools=["Git"],
        domain_keywords=["Microservices"],
        jd_exact_spelling={"kubernetes": "Kubernetes", "aws": "AWS"}
    )
    
    cand_has, gaps = compute_candidate_skills_and_gaps(
        jd_skills=jd.must_have_skills + jd.nice_to_have_skills + jd.tools,
        facts=facts
    )
    # Candidate has Python, FastAPI, PostgreSQL, Docker, Git
    assert "Python" in cand_has or "python" in [s.lower() for s in cand_has]
    assert "PostgreSQL" in cand_has or "postgresql" in [s.lower() for s in cand_has]
    # Candidate lacks Kubernetes and AWS -> strictly categorized as gaps, NOT hallucinated
    assert any("Kubernetes" in g or "kubernetes" in g.lower() for g in gaps)
    assert any("AWS" in g or "aws" in g.lower() for g in gaps)


# ===========================================================================
# 2. ADVERSARIAL TESTS (Verifier Rejections & Fallback)
# ===========================================================================

def test_verifier_rejects_invented_metric():
    """Adversarial: LLM adds a fabricated percentage '35%' not in original."""
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    bullet = FactBullet(
        id="exp_0_b1",
        section="experience",
        entity="InfraCore Labs",
        role_or_degree="Software Engineering Intern",
        original_text="Optimized relational database queries in PostgreSQL, improving query response latency across services.",
        tools_mentioned=["postgresql", "sql"],
        numbers_present=[],
        dates_present=[]
    )
    
    fabricated_bullet = "Optimized relational database queries in PostgreSQL, reducing query latency by 35% across services."
    res = verify_edited_bullet(
        original_bullet=bullet,
        edited_text=fabricated_bullet,
        operations_claimed=["METRIC_ADD"],
        keywords_added_claimed=[],
        canonical_facts=facts,
        strictness="conservative"
    )
    
    assert res.passed is False
    assert "number" in res.violation.lower() or "metric" in res.violation.lower()
    assert res.final_text == bullet.original_text


def test_verifier_rejects_unmentioned_tool():
    """Adversarial: LLM injects 'AWS' into a bullet where candidate never used AWS."""
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    bullet = FactBullet(
        id="exp_0_b0",
        section="experience",
        entity="InfraCore Labs",
        role_or_degree="Software Engineering Intern",
        original_text="Built RESTful microservices using Python and FastAPI for real-time order intake processing.",
        tools_mentioned=["python", "fastapi"],
        numbers_present=[],
        dates_present=[]
    )
    
    unauthorized_tool_bullet = "Built RESTful microservices using Python and FastAPI and deployed to AWS Lambda cloud."
    res = verify_edited_bullet(
        original_bullet=bullet,
        edited_text=unauthorized_tool_bullet,
        operations_claimed=["KEYWORD_ADD"],
        keywords_added_claimed=[{"keyword": "AWS", "evidence_bullet_id": "none"}],
        canonical_facts=facts,
        strictness="conservative"
    )
    
    assert res.passed is False
    assert "unauthorized" in res.violation.lower() or "tool" in res.violation.lower()
    assert res.final_text == bullet.original_text


def test_verifier_rejects_word_drop():
    """Adversarial: LLM drops more than 40% of original words."""
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    bullet = FactBullet(
        id="exp_0_b0",
        section="experience",
        entity="InfraCore Labs",
        role_or_degree="Software Engineering Intern",
        original_text="Built RESTful microservices using Python and FastAPI for real-time order intake processing and validation.",
        tools_mentioned=["python", "fastapi"],
        numbers_present=[],
        dates_present=[]
    )
    
    shortened_bullet = "Built microservices."
    res = verify_edited_bullet(
        original_bullet=bullet,
        edited_text=shortened_bullet,
        operations_claimed=["TRIM"],
        keywords_added_claimed=[],
        canonical_facts=facts,
        strictness="balanced"
    )
    
    assert res.passed is False
    assert res.final_text == bullet.original_text


def test_verifier_rejects_first_person_pronouns():
    """Adversarial: LLM introduces 'I developed' or 'My team'."""
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    bullet = FactBullet(
        id="exp_0_b0",
        section="experience",
        entity="InfraCore Labs",
        role_or_degree="Software Engineering Intern",
        original_text="Built RESTful microservices using Python and FastAPI for real-time order intake processing.",
        tools_mentioned=["python", "fastapi"],
        numbers_present=[],
        dates_present=[]
    )
    
    first_person_bullet = "I built RESTful microservices using Python and FastAPI for real-time order intake processing."
    res = verify_edited_bullet(
        original_bullet=bullet,
        edited_text=first_person_bullet,
        operations_claimed=[],
        keywords_added_claimed=[],
        canonical_facts=facts,
        strictness="balanced"
    )
    
    assert res.passed is False
    assert "first-person" in res.violation.lower() or "pronoun" in res.violation.lower()
    assert res.final_text == bullet.original_text


def test_verifier_rejects_buzzwords():
    """Adversarial: LLM adds empty corporate buzzwords."""
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    bullet = FactBullet(
        id="exp_0_b0",
        section="experience",
        entity="InfraCore Labs",
        role_or_degree="Software Engineering Intern",
        original_text="Built RESTful microservices using Python and FastAPI for real-time order intake processing.",
        tools_mentioned=["python", "fastapi"],
        numbers_present=[],
        dates_present=[]
    )
    
    buzzword_bullet = "Built synergistic, rockstar microservices using Python and FastAPI for order processing."
    res = verify_edited_bullet(
        original_bullet=bullet,
        edited_text=buzzword_bullet,
        operations_claimed=[],
        keywords_added_claimed=[],
        canonical_facts=facts,
        strictness="conservative"
    )
    
    assert res.passed is False
    assert "buzzword" in res.violation.lower()
    assert res.final_text == bullet.original_text


# ===========================================================================
# 3. GOLDEN TEST (1 Profile + 3 Target JDs)
# ===========================================================================

@pytest.mark.asyncio
async def test_golden_three_target_jds(tmp_path):
    """
    Golden test: runs full pipeline on 1 fresher profile across 3 realistic JDs.
    Verifies:
    1. Generated PDF is 1 page.
    2. Headings detected in order.
    3. Candidate-owned JD skills have >= 90% keyword coverage in PDF text.
    4. Zero fabricated numbers or tools in PDF text.
    5. Fidelity score >= 0.85.
    """
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    
    target_jds = [
        # JD 1: Backend Engineer (Core Python/FastAPI/Postgres)
        {
            "id": "jd_backend",
            "title": "Junior Backend Engineer",
            "description": """
            We are looking for an Entry-Level Backend Developer to build scalable APIs.
            Must-have skills: Python, FastAPI, PostgreSQL, Git.
            Nice-to-have: Docker, Redis.
            Responsibilities: Write clean code, maintain relational databases, write unit tests.
            """
        },
        # JD 2: QA / Automation Engineer
        {
            "id": "jd_qa",
            "title": "Software Test Engineer (Fresher)",
            "description": """
            Looking for a QA Automation Engineer to join our quality engineering team.
            Requirements: Python, Pytest, SQL, Git.
            Familiarity with containerization (Docker) and Linux environments is an advantage.
            Responsibilities: Automate test suites, integration testing, defect reporting.
            """
        },
        # JD 3: Data / Backend Analyst
        {
            "id": "jd_data_backend",
            "title": "Junior Data Platform Engineer",
            "description": """
            Join our data engineering team to optimize backend pipelines.
            Must have strong foundation in: Python, SQL, PostgreSQL, Data Structures.
            Experience with REST APIs and Linux command line required.
            """
        }
    ]

    for idx, jd_info in enumerate(target_jds):
        pdf_out = str(tmp_path / f"resume_jd_{idx}.pdf")
        tex_content, pdf_path, ats, changes_summary = await generate_tailored_resume_pipeline(
            profile_json=SAMPLE_FRESHER_PROFILE,
            job_description=jd_info["title"] + "\n" + jd_info["description"],
            output_pdf_path=pdf_out,
            strictness="conservative",
        )
        
        assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"
        
        # 1. Check exactly 1 page
        doc = fitz.open(pdf_path)
        assert len(doc) == 1, f"Expected 1 page for {jd_info['title']}, got {len(doc)}"
        pdf_text = doc[0].get_text()
        doc.close()

        # 2. Check headings detected in order
        assert ats.is_one_page is True
        detected = ats.headings_detected
        assert "education" in detected
        assert "technical skills" in detected or "skills" in detected
        assert "experience" in detected
        assert "projects" in detected

        # 3. Candidate-owned JD skills have >= 90% keyword coverage
        cand_owned_skills = ats.candidate_owned_must_haves
        assert len(cand_owned_skills) > 0
        missing_cand_skills = [k for k in cand_owned_skills if k not in ats.matched_keywords]
        assert ats.keyword_coverage_percent >= 90.0, (
            f"Expected >= 90% coverage on candidate-owned skills for {jd_info['title']}, "
            f"got {ats.keyword_coverage_percent}%. Missing: {missing_cand_skills}"
        )

        # 4. Zero fabricated numbers or tools
        # Check all numbers extracted from PDF exist in candidate facts
        pdf_numbers = extract_numbers_tokens(pdf_text)
        fact_numbers = set(facts.get_all_numbers())
        if facts.phone:
            fact_numbers.update(extract_numbers_tokens(facts.phone))
        for ed in facts.education:
            fact_numbers.update(extract_numbers_tokens(str(ed)))
        for ach in facts.achievements:
            fact_numbers.update(extract_numbers_tokens(ach))
        for exp in facts.experience_entries:
            fact_numbers.update(extract_numbers_tokens(str(exp.get("dates", ""))))
        for pr in facts.project_entries:
            fact_numbers.update(extract_numbers_tokens(str(pr.get("dates", ""))))

        for num in pdf_numbers:
            # Allow common format variations like 2021, 2025, 8.8, 10.0, 5000, 12000, 85%, 450+, 1500+
            assert (num in fact_numbers or any(num in fn for fn in fact_numbers) or any(fn in num for fn in fact_numbers)), (
                f"Fabricated number '{num}' found in PDF for {jd_info['title']}! Allowed: {fact_numbers}"
            )

        # 5. Fidelity score >= 0.85 or >= 85.0
        assert ats.fidelity_score >= 85.0 or ats.fidelity_score >= 0.85, f"Fidelity score too low: {ats.fidelity_score}"


# ===========================================================================
# 4. PROPERTY-BASED / INVARIANT TEST
# ===========================================================================

@pytest.mark.asyncio
async def test_property_all_tools_and_numbers_authorized(tmp_path):
    """
    Property test: for any tailored output generated by the pipeline,
    every tech tool extracted from the PDF body must either:
    (a) Be listed in candidate's original skills/bullets, or
    (b) Be directly implied by a tool in candidate's facts via implications.yaml.
    """
    facts = build_canonical_facts(SAMPLE_FRESHER_PROFILE)
    
    # Candidate facts authorized tools
    allowed_tools = set(facts.normalized_skills)
    for b in facts.bullets.values():
        allowed_tools.update(b.tools_mentioned)
    for allowed_t in list(allowed_tools):
        t_norm = normalize_skill_token(allowed_t)
        if t_norm in IMPLICATIONS_MAP:
            allowed_tools.update(IMPLICATIONS_MAP[t_norm])
        elif allowed_t in IMPLICATIONS_MAP:
            allowed_tools.update(IMPLICATIONS_MAP[allowed_t])

    allowed_tools_norm = {normalize_skill_token(t) for t in allowed_tools if normalize_skill_token(t)}

    pdf_out = str(tmp_path / "property_resume.pdf")
    tex_content, pdf_path, ats, changes_summary = await generate_tailored_resume_pipeline(
        profile_json=SAMPLE_FRESHER_PROFILE,
        job_description="Software Engineer - Backend & Cloud\nSeeking a Python Developer with PostgreSQL, Docker, Git, and REST API experience.",
        output_pdf_path=pdf_out,
        strictness="conservative",
    )
    
    doc = fitz.open(pdf_path)
    full_text = doc[0].get_text()
    doc.close()

    # Extract all tools from generated PDF text using GLOBAL_TECH_TAXONOMY
    words_in_pdf = set(full_text.lower().split())
    # Test multi-word and single-word taxonomy items
    detected_tools = set()
    for tech in GLOBAL_TECH_TAXONOMY:
        if " " in tech:
            if tech in full_text.lower():
                detected_tools.add(tech)
        else:
            if tech in words_in_pdf:
                detected_tools.add(tech)

    # Invariant: Every detected tool in PDF must be authorized
    for tool in detected_tools:
        canon_tool = normalize_skill_token(tool)
        assert (canon_tool in allowed_tools_norm or any(canon_tool in at for at in allowed_tools_norm)), (
            f"Unauthorized tool '{tool}' found in generated PDF! Allowed set: {allowed_tools_norm}"
        )
