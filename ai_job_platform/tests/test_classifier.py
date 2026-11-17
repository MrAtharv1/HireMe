"""
Comprehensive tests for 3-Stage Fresher Job Classifier.
Contains >= 30 labeled test cases verifying:
- Senior titles/roles rejected
- Fresher/Junior/Intern roles allowed
- Experience extraction bounds
- Description reject phrases
- Fresher score calculations
"""

import pytest
from app.services.job_classifier import (
    check_stage1_rules,
    compute_fresher_score,
    extract_years_of_experience,
)

# 30+ Labeled Job Samples
TEST_JOBS = [
    # --- Senior / Lead / Architecture (Must be rejected) ---
    {"title": "Senior Software Engineer", "desc": "Build scalable systems.", "expected_pass": False},
    {"title": "Sr. Backend Developer", "desc": "Work with Python and Postgres.", "expected_pass": False},
    {"title": "Lead Full Stack Engineer", "desc": "Lead our core web team.", "expected_pass": False},
    {"title": "Staff Engineer - Distributed Systems", "desc": "Architect high throughput APIs.", "expected_pass": False},
    {"title": "Principal Architect", "desc": "Define long term cloud architecture.", "expected_pass": False},
    {"title": "Head of Engineering", "desc": "Manage the engineering organization.", "expected_pass": False},
    {"title": "Engineering Director", "desc": "Oversee multiple product squads.", "expected_pass": False},
    {"title": "VP of Technology", "desc": "Executive tech leadership.", "expected_pass": False},
    {"title": "Engineering Manager", "desc": "People manager for 8 engineers.", "expected_pass": False},
    {"title": "Enterprise Cloud Architect", "desc": "Design enterprise topologies.", "expected_pass": False},
    {"title": "Distinguished Engineer", "desc": "Company-wide technical authority.", "expected_pass": False},
    {"title": "SDE II", "desc": "Mid-level backend services.", "expected_pass": False},
    {"title": "Software Engineer III", "desc": "Deep system design skills.", "expected_pass": False},
    {"title": "Backend Developer IV", "desc": "Lead large migrations.", "expected_pass": False},
    {"title": "SDE-2 - Payments", "desc": "Core payment processing pipeline.", "expected_pass": False},
    {"title": "Management Consultant", "desc": "Strategy consulting.", "expected_pass": False},

    # --- Senior description / Experience requirements (Must be rejected) ---
    {"title": "Software Developer", "desc": "Requires 5+ years of experience in microservices.", "expected_pass": False},
    {"title": "Python Developer", "desc": "Candidate must have 3-5 years of experience with Django.", "expected_pass": False},
    {"title": "DevOps Engineer", "desc": "Minimum 4 years of professional experience in Kubernetes.", "expected_pass": False},
    {"title": "Frontend Engineer", "desc": "Proven track record of leading teams of 5+ devs.", "expected_pass": False},
    {"title": "Fullstack Developer", "desc": "Must mentor junior engineers and review PRs.", "expected_pass": False},
    {"title": "Systems Engineer", "desc": "Expected to own architecture for our cloud platform.", "expected_pass": False},

    # --- Freshers / Interns / Graduates (Must be accepted) ---
    {"title": "Software Engineering Intern", "desc": "Internship for summer 2026.", "expected_pass": True},
    {"title": "Frontend Developer Intern", "desc": "Learn React and modern web development.", "expected_pass": True},
    {"title": "Graduate Engineer Trainee (GET)", "desc": "Training program for fresh engineering graduates.", "expected_pass": True},
    {"title": "Graduate Trainee - QA", "desc": "Join our testing automation graduate batch.", "expected_pass": True},
    {"title": "Entry Level Python Developer", "desc": "0-1 years of experience or enthusiastic freshers.", "expected_pass": True},
    {"title": "Junior Backend Developer", "desc": "Requires 0-2 years of experience in Node.js.", "expected_pass": True},
    {"title": "Jr. Data Analyst", "desc": "Work with SQL and Python pandas. 1 year experience.", "expected_pass": True},
    {"title": "Associate Software Engineer", "desc": "Entry level engineering position for 2025/2026 batch.", "expected_pass": True},
    {"title": "Fresher Java Developer", "desc": "Core Java basics and OOP knowledge required.", "expected_pass": True},
    {"title": "Campus Hire - 2026 Batch", "desc": "Open to B.Tech/B.E graduates with no prior experience.", "expected_pass": True},
    {"title": "New Grad Software Engineer", "desc": "0 to 1 years of experience with Python/Go.", "expected_pass": True},
    {"title": "Associate Consultant", "desc": "Entry role for fresh business/tech grads.", "expected_pass": True},
    {"title": "Web Developer", "desc": "No experience required. Freshers welcome!", "expected_pass": True},
]


@pytest.mark.parametrize("job", TEST_JOBS)
def test_stage1_classification_on_labeled_dataset(job):
    result = check_stage1_rules(job["title"], job["desc"])
    assert result["passed"] == job["expected_pass"], (
        f"Failed for job '{job['title']}': expected {job['expected_pass']}, got {result['passed']}. "
        f"Reason: {result['reason']}"
    )


def test_experience_extraction_bounds():
    min_yr, max_yr = extract_years_of_experience("Requires 3+ years of relevant experience.")
    assert min_yr == 3
    assert max_yr is None

    min_yr, max_yr = extract_years_of_experience("Candidate must have 0-2 years experience.")
    assert min_yr == 0
    assert max_yr == 2

    min_yr, max_yr = extract_years_of_experience("Minimum 5 years of professional work experience.")
    assert min_yr == 5

    min_yr, max_yr = extract_years_of_experience("Freshers welcome / 0 to 1 years.")
    assert min_yr == 0
    assert max_yr == 1

    min_yr, max_yr = extract_years_of_experience("No prior experience required.")
    assert min_yr == 0


def test_fresher_score_calculation():
    # Perfect fresher role: Intern, 0 years, allow title signal, matching candidate skills
    score, match_pct, matched, missing, reason = compute_fresher_score(
        seniority="intern",
        min_years=0,
        title="Software Engineering Intern",
        description="Python, SQL, React internship for freshers.",
        candidate_skills=["Python", "SQL", "Git"],
        required_skills=["Python", "SQL"],
        nice_to_have_skills=["React"]
    )
    # 40 (intern) + 25 (0 yrs) + 10 (title allow) + 16-20 (skills) >= 85
    assert score >= 85
    assert "Python" in matched
    assert "SQL" in matched
    assert score >= 60  # Passes fresher threshold

    # Senior role with 5 years
    score_sr, _, _, _, _ = compute_fresher_score(
        seniority="senior",
        min_years=5,
        title="Senior Tech Lead",
        description="Must have 5+ years building architectures.",
        candidate_skills=["Python"],
    )
    assert score_sr < 60  # Rejected by threshold
