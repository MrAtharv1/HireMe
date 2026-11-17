"""
End-to-End Integration Test for Fresher Job Platform (Part G).
Tests:
1. Sample profile canonical fact extraction.
2. 3-stage classification across a mixed batch of jobs (senior dropped, fresher kept).
3. LaTeX resume rendering for a top-matching fresher job.
4. ATS Verification asserting:
   - Extractable section headings: Education, Skills, Projects, Experience
   - Page count == 1
   - ATS score >= 80.0
"""

import pytest
import fitz
from app.services.facts_store import build_canonical_facts
from app.services.job_classifier import check_stage1_rules, compute_fresher_score
from app.services.latex_renderer import render_latex_resume, estimate_line_budget
from app.services.resume_tailor_pipeline import categorize_skills
from app.services.ats_verifier import verify_pdf_ats_compliance

SAMPLE_CANDIDATE = {
    "personal_info": {
        "name": "Arjun Sharma",
        "email": "arjun.sharma@example.com",
        "phone": "+91 98765 43210",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/arjunsharma",
        "github": "https://github.com/arjunsharma",
    },
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "React", "Data Structures & Algorithms"],
    "education": [
        {
            "institution": "National Institute of Engineering",
            "degree": "B.E. in Information Science & Engineering",
            "dates": "2021 - 2025",
            "location": "Mysuru, India",
        }
    ],
    "experience": [
        {
            "company": "NextGen Software",
            "role": "Backend Engineering Intern",
            "dates": "Jan 2024 - Jun 2024",
            "bullets": [
                "Engineered RESTful API microservices in Python and FastAPI for applicant tracking.",
                "Optimized SQL query performance in PostgreSQL reducing response latency."
            ]
        }
    ],
    "projects": [
        {
            "name": "Cloud Job Portal",
            "technologies": ["Python", "FastAPI", "React", "Docker"],
            "dates": "Aug 2024 - Oct 2024",
            "bullets": [
                "Built full-stack job recommendation portal with FastAPI backend and React frontend.",
                "Containerized development services with Docker and automated deployment workflows."
            ]
        },
        {
            "name": "Algorithmic Cache Engine",
            "technologies": ["Python", "Data Structures & Algorithms"],
            "dates": "Nov 2024",
            "bullets": [
                "Implemented high-performance LRU cache in Python with thread-safe access mechanics."
            ]
        }
    ],
    "certifications": ["AWS Certified Cloud Practitioner"],
    "achievements": ["Finalist in National Smart India Hackathon 2024"],
}

MIXED_JOB_BATCH = [
    {
        "id": "job_sr_1",
        "title": "Principal Architect - Cloud Infrastructure",
        "company": "BigTech Cloud",
        "description": "Requires 8+ years experience designing enterprise cloud infrastructure and leading teams.",
        "senior": True,
    },
    {
        "id": "job_sr_2",
        "title": "Senior Staff Backend Developer",
        "company": "Fintech Global",
        "description": "Must have 5+ years building distributed financial services and mentoring juniors.",
        "senior": True,
    },
    {
        "id": "job_fresh_1",
        "title": "Graduate Engineer Trainee (GET) - Software",
        "company": "Razorpay",
        "description": "0-1 years experience or 2025 batch graduates. Hands-on coding in Python, SQL, REST APIs.",
        "senior": False,
    },
    {
        "id": "job_fresh_2",
        "title": "Software Engineering Intern - Backend",
        "company": "Swiggy",
        "description": "Summer internship for pre-final/final year students with Python/FastAPI knowledge.",
        "senior": False,
    },
]


def test_integration_flow(tmp_path):
    # Step 1: Ingest and verify candidate facts
    facts = build_canonical_facts(SAMPLE_CANDIDATE)
    assert facts.name == "Arjun Sharma"
    assert "python" in facts.normalized_skills
    assert "fastapi" in facts.normalized_skills

    # Step 2: Run classification across mixed batch
    accepted_fresher_jobs = []
    rejected_senior_jobs = []

    for job in MIXED_JOB_BATCH:
        stage1 = check_stage1_rules(job["title"], job["description"])
        if stage1["passed"]:
            fresher_score, match_pct, matched, missing, reason = compute_fresher_score(
                seniority="intern" if stage1["is_obvious_fresher"] else "entry",
                min_years=stage1["min_years"],
                title=job["title"],
                description=job["description"],
                candidate_skills=facts.canonical_skills,
                required_skills=["Python", "FastAPI", "SQL"],
            )
            if fresher_score >= 60:
                accepted_fresher_jobs.append((job, fresher_score, match_pct))
            else:
                rejected_senior_jobs.append(job)
        else:
            rejected_senior_jobs.append(job)

    # Assert all senior roles are rejected and all fresher roles are accepted
    assert len(rejected_senior_jobs) == 2
    assert {j["id"] for j in rejected_senior_jobs} == {"job_sr_1", "job_sr_2"}

    assert len(accepted_fresher_jobs) == 2
    assert {j[0]["id"] for j in accepted_fresher_jobs} == {"job_fresh_1", "job_fresh_2"}

    # Pick the top fresher job
    top_job, f_score, m_pct = accepted_fresher_jobs[0]
    assert f_score >= 70

    # Step 3: Render tailored LaTeX resume
    skills_cat = categorize_skills(facts.canonical_skills, ["Python", "FastAPI", "SQL"])
    render_payload = {
        "name": facts.name,
        "email": facts.email,
        "phone": facts.phone,
        "location": facts.location,
        "linkedin": facts.linkedin,
        "github": facts.github,
        "portfolio": facts.portfolio,
        "summary": "Aspiring Software Engineer with strong foundation in Python, FastAPI, and PostgreSQL.",
        "education": facts.education,
        "skills_categories": skills_cat,
        "certifications": facts.certifications,
        "achievements": facts.achievements,
        "experiences": [
            {
                "role": "Backend Engineering Intern",
                "company": "NextGen Software",
                "dates": "Jan 2024 - Jun 2024",
                "location": "Bengaluru",
                "bullets": [
                    "Engineered RESTful API microservices in Python and FastAPI for applicant tracking.",
                    "Optimized SQL query performance in PostgreSQL reducing response latency."
                ]
            }
        ],
        "projects": [
            {
                "name": "Cloud Job Portal",
                "technologies_str": "Python, FastAPI, React, Docker",
                "dates": "Aug 2024 - Oct 2024",
                "bullets": [
                    "Built full-stack job recommendation portal with FastAPI backend and React frontend.",
                    "Containerized development services with Docker and automated deployment workflows."
                ]
            }
        ]
    }

    tex_source = render_latex_resume(render_payload)
    assert r"\section{Education}" in tex_source
    assert r"\section{Technical Skills}" in tex_source
    assert r"\section{Experience}" in tex_source
    assert r"\section{Projects}" in tex_source
    assert estimate_line_budget(render_payload) <= 52

    # Step 4: Generate synthetic compiled 1-page PDF to test ATS verification
    pdf_path = str(tmp_path / "tailored_arjun.pdf")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    
    resume_body_text = (
        "Arjun Sharma\n"
        "arjun.sharma@example.com | +91 98765 43210 | Bengaluru, India\n\n"
        "Education\n"
        "National Institute of Engineering - B.E. in Information Science (2021 - 2025)\n\n"
        "Technical Skills\n"
        "Languages: Python, SQL\n"
        "Frameworks: FastAPI, React\n"
        "Databases: PostgreSQL\n"
        "Tools & Cloud: Docker, Git\n\n"
        "Experience\n"
        "Backend Engineering Intern - NextGen Software (Jan 2024 - Jun 2024)\n"
        "Engineered RESTful API microservices in Python and FastAPI for applicant tracking.\n"
        "Optimized SQL query performance in PostgreSQL reducing response latency.\n\n"
        "Projects\n"
        "Cloud Job Portal (Python, FastAPI, React, Docker)\n"
        "Built full-stack job recommendation portal with FastAPI backend and React frontend.\n"
        "Containerized development services with Docker and automated deployment workflows.\n\n"
        "Certifications\n"
        "AWS Certified Cloud Practitioner\n"
    )
    page.insert_text((40, 50), resume_body_text, fontsize=10.5)
    doc.save(pdf_path)
    doc.close()

    # Step 5: Run ATS Verification
    ats_report = verify_pdf_ats_compliance(
        pdf_path=pdf_path,
        jd_must_have_skills=["Python", "FastAPI", "SQL"],
        canonical_facts=facts
    )

    assert ats_report.is_one_page is True
    assert ats_report.page_count == 1
    assert "education" in ats_report.headings_detected
    assert "technical skills" in ats_report.headings_detected or "skills" in ats_report.headings_detected
    assert "experience" in ats_report.headings_detected
    assert "projects" in ats_report.headings_detected
    assert ats_report.ats_score >= 80.0
    assert ats_report.passed is True
