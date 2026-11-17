"""
Tests for LaTeX Resume Tailoring Pipeline (Part E).
Verifies:
- Canonical Facts store and stable bullet IDs
- LaTeX character escaping
- Jake's template rendering and standard headings
- 1-page line budget auto-fitting
- Skill categorization (0 hallucinated skills)
- PyMuPDF ATS verification
"""

import pytest
import fitz
from app.services.facts_store import build_canonical_facts, normalize_skill_token, resolve_canonical_skill_name
from app.services.latex_renderer import latex_escape, render_latex_resume, estimate_line_budget, auto_fit_to_one_page
from app.services.resume_tailor_pipeline import categorize_skills
from app.services.ats_verifier import verify_pdf_ats_compliance

SAMPLE_PROFILE = {
    "personal_info": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/janedoe",
        "github": "https://github.com/janedoe",
    },
    "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "Git", "Data Structures & Algorithms"],
    "education": [
        {
            "institution": "National Institute of Technology",
            "degree": "B.Tech in Computer Science",
            "dates": "2021 - 2025",
            "location": "Surathkal, India",
        }
    ],
    "experience": [
        {
            "company": "TechStart Inc",
            "role": "Software Engineering Intern",
            "dates": "May 2024 - Aug 2024",
            "bullets": [
                "Developed RESTful backend APIs using Python and FastAPI for real-time order processing.",
                "Optimized database queries in PostgreSQL, improving response time for high-volume transactions."
            ]
        }
    ],
    "projects": [
        {
            "name": "Job Platform MVP",
            "technologies": ["Python", "FastAPI", "React", "Docker"],
            "dates": "Jan 2025",
            "bullets": [
                "Engineered responsive job discovery platform using React frontend and FastAPI microservices.",
                "Containerized development services with Docker and implemented automated test suites."
            ]
        },
        {
            "name": "Distributed Cache",
            "technologies": ["Python", "Redis"],
            "dates": "Nov 2024",
            "bullets": [
                "Implemented in-memory LRU key-value cache in Python with TTL expiration mechanics."
            ]
        }
    ],
    "certifications": ["AWS Certified Cloud Practitioner"],
    "achievements": ["Ranked top 5% in University Coding Hackathon 2024"],
}


def test_canonical_facts_store():
    facts = build_canonical_facts(SAMPLE_PROFILE)
    assert facts.name == "Jane Doe"
    assert "python" in facts.normalized_skills
    assert "fastapi" in facts.normalized_skills
    
    # Stable bullet IDs
    assert "exp_0_b0" in facts.bullets
    assert "proj_0_b0" in facts.bullets
    assert facts.bullets["exp_0_b0"].section == "experience"
    assert facts.bullets["proj_0_b0"].section == "projects"
    assert "FastAPI" in facts.bullets["exp_0_b0"].original_text


def test_latex_escape():
    raw = r"100% pure $C&#_^{}~\""
    escaped = latex_escape(raw)
    assert r"\%" in escaped
    assert r"\$" in escaped
    assert r"\&" in escaped
    assert r"\#" in escaped
    assert r"\_" in escaped
    assert r"\textasciicircum{}" in escaped
    assert r"\textasciitilde{}" in escaped


def test_render_latex_resume():
    facts = build_canonical_facts(SAMPLE_PROFILE)
    skills_cat = categorize_skills(facts.canonical_skills, ["Python", "FastAPI", "PostgreSQL"])
    
    payload = {
        "name": facts.name,
        "email": facts.email,
        "phone": facts.phone,
        "location": facts.location,
        "linkedin": facts.linkedin,
        "github": facts.github,
        "portfolio": facts.portfolio,
        "summary": "Software engineer with background in Python and FastAPI.",
        "education": facts.education,
        "skills_categories": skills_cat,
        "certifications": facts.certifications,
        "achievements": facts.achievements,
        "experiences": [
            {
                "role": "Software Engineering Intern",
                "company": "TechStart Inc",
                "dates": "May 2024 - Aug 2024",
                "location": "Bengaluru",
                "bullets": ["Engineered RESTful backend APIs using Python and FastAPI."]
            }
        ],
        "projects": [
            {
                "name": "Job Platform MVP",
                "technologies_str": "Python, FastAPI, React",
                "dates": "Jan 2025",
                "bullets": ["Built responsive interface with React and FastAPI services."]
            }
        ]
    }
    
    tex = render_latex_resume(payload)
    assert r"\documentclass[letterpaper,10pt]{article}" in tex
    assert "Jane Doe" in tex
    assert r"\section{Education}" in tex
    assert r"\section{Technical Skills}" in tex
    assert r"\section{Experience}" in tex
    assert r"\section{Projects}" in tex


def test_skill_categorization_no_hallucinations():
    cand_skills = ["Python", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "DSA"]
    jd_skills = ["Python", "PostgreSQL", "AWS"]
    
    categories = categorize_skills(cand_skills, jd_skills)
    
    # Must never hallucinate skills not in cand_skills
    all_cat_skills = []
    for s_list in categories.values():
        all_cat_skills.extend(s_list)
    
    assert set(resolve_canonical_skill_name(s) for s in all_cat_skills) == set(resolve_canonical_skill_name(s) for s in cand_skills)
    assert "AWS" not in all_cat_skills  # AWS was in JD, but candidate does not have it!
    assert "Python" in categories["Languages"]
    assert "FastAPI" in categories["Frameworks & Libraries"]
    assert "PostgreSQL" in categories["Databases"]


def test_one_page_line_budget_and_auto_fit():
    payload = {
        "summary": "Long summary",
        "education": [{"inst": "NIT"}],
        "skills_categories": {"Languages": ["Python"], "Databases": ["PostgreSQL"]},
        "experiences": [{"role": "Dev", "bullets": ["b1", "b2", "b3"]}],
        "projects": [
            {"name": "P1", "bullets": ["b1", "b2", "b3", "b4"]},
            {"name": "P2", "bullets": ["b1", "b2", "b3", "b4"]},
            {"name": "P3", "bullets": ["b1", "b2", "b3", "b4"]},
        ],
        "certifications": ["Cert 1", "Cert 2"],
        "achievements": ["Ach 1"]
    }
    
    initial_lines = estimate_line_budget(payload)
    fitted = auto_fit_to_one_page(payload, max_lines=40)
    fitted_lines = estimate_line_budget(fitted)
    
    assert fitted_lines <= 40 or fitted_lines < initial_lines


def test_ats_verification_with_pymupdf(tmp_path):
    # Generate a minimal 1-page PDF using PyMuPDF to test the ATS verification engine
    pdf_path = str(tmp_path / "test_resume.pdf")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    
    text = (
        "Jane Doe\n"
        "jane@example.com | +91 9876543210\n\n"
        "Education\n"
        "National Institute of Technology\n\n"
        "Technical Skills\n"
        "Languages: Python, SQL\n"
        "Frameworks: FastAPI, React\n"
        "Databases: PostgreSQL\n\n"
        "Experience\n"
        "Software Engineering Intern - TechStart Inc\n"
        "Engineered RESTful backend APIs with Python and FastAPI.\n\n"
        "Projects\n"
        "Job Platform MVP\n"
        "Containerized services with Docker and implemented pytest suites.\n\n"
        "Certifications\n"
        "AWS Certified Cloud Practitioner\n"
    )
    
    page.insert_text((50, 60), text, fontsize=11)
    doc.save(pdf_path)
    doc.close()
    
    facts = build_canonical_facts(SAMPLE_PROFILE)
    report = verify_pdf_ats_compliance(
        pdf_path=pdf_path,
        jd_must_have_skills=["Python", "FastAPI", "PostgreSQL"],
        canonical_facts=facts
    )
    
    assert report.is_one_page is True
    assert report.page_count == 1
    assert "education" in report.headings_detected
    assert "experience" in report.headings_detected
    assert "Python" in report.matched_keywords
    assert "FastAPI" in report.matched_keywords
    assert report.ats_score >= 80.0
    assert report.passed is True


@pytest.mark.asyncio
async def test_compile_latex_to_pdf_fallback(tmp_path):
    """Verifies that compile_latex_to_pdf always compiles a valid 1-page PDF."""
    from pathlib import Path
    from app.services.latex_compiler import compile_latex_to_pdf
    from app.services.latex_renderer import render_latex_resume, render_html_resume

    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+91 9876543210",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/janedoe",
        "github": "https://github.com/janedoe",
        "summary": "Software Engineer specializing in Python and FastAPI.",
        "education": [{"institution": "NIT Surathkal", "dates": "2021 - 2025", "degree": "B.Tech CS", "location": "Surathkal"}],
        "skills_categories": {"Languages": ["Python", "SQL"], "Frameworks": ["FastAPI", "React"]},
        "experiences": [{"role": "Intern", "company": "TechStart", "dates": "2024", "location": "BLR", "bullets": ["Built REST APIs"]}],
        "projects": [{"name": "Platform MVP", "technologies_str": "FastAPI, React", "dates": "2025", "bullets": ["Shipped app"]}],
        "certifications": ["AWS Cloud Practitioner"],
        "achievements": ["Dean's List"],
    }

    tex_content = render_latex_resume(payload)
    output_pdf = str(tmp_path / "test_out.pdf")

    tex_path, pdf_path = await compile_latex_to_pdf(
        tex_content=tex_content,
        output_pdf_path=output_pdf,
        render_payload=payload
    )

    assert Path(tex_path).is_file()
    assert Path(pdf_path).is_file()

    doc = fitz.open(pdf_path)
    assert len(doc) == 1
    text = doc[0].get_text()
    assert "Jane Doe" in text
    assert "Education" in text
    assert "Technical Skills" in text
    assert "Experience" in text
    assert "Projects" in text

