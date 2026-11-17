import pytest
from datetime import datetime, timezone

from app.services.job_sources.base import RawJob, clean_html_text, is_valid_http_url
from app.services.job_sources.ats_boards import load_companies
from app.services.job_aggregator import deduplicate_raw_jobs, are_jobs_fuzzy_duplicates


def test_clean_html_text():
    html = "<p>Join our team as a <b>Software Engineer</b>! <script>alert('x')</script> &amp; grow.</p>"
    clean = clean_html_text(html)
    assert clean == "Join our team as a Software Engineer! & grow."
    assert "<script>" not in clean


def test_is_valid_http_url():
    assert is_valid_http_url("https://careers.google.com/jobs/123") is True
    assert is_valid_http_url("http://example.com/apply") is True
    assert is_valid_http_url("ftp://example.com") is False
    assert is_valid_http_url("invalid-url") is False
    assert is_valid_http_url("") is False
    assert is_valid_http_url(None) is False


def test_raw_job_validation():
    job = RawJob(
        title="Graduate Engineer Trainee",
        company="Razorpay",
        location="Bangalore",
        remote=False,
        description="<b>Exciting opportunity</b> for freshers.",
        apply_url="https://razorpay.com/careers/get",
        source="greenhouse",
        source_job_id="rzp_101",
    )
    assert job.title == "Graduate Engineer Trainee"
    assert job.description == "Exciting opportunity for freshers."


def test_deduplicate_raw_jobs():
    aggregator_job = RawJob(
        title="Junior Backend Developer",
        company="Razorpay Software Pvt Ltd",
        location="Bangalore, India",
        remote=False,
        description="Backend role with Python and FastAPI.",
        apply_url="https://jooble.org/job/123",
        source="jooble",
        source_job_id="j_123",
    )
    direct_ats_job = RawJob(
        title="Junior Backend Developer",
        company="Razorpay",
        location="Bangalore",
        remote=False,
        description="Backend role with Python and FastAPI.",
        apply_url="https://boards.greenhouse.io/razorpay/jobs/456",
        source="greenhouse",
        source_job_id="rzp_456",
    )
    different_job = RawJob(
        title="QA Automation Engineer",
        company="Swiggy",
        location="Remote",
        remote=True,
        description="Quality assurance and testing.",
        apply_url="https://swiggy.com/careers/qa",
        source="greenhouse",
        source_job_id="swg_789",
    )

    # They should match as fuzzy duplicates
    assert are_jobs_fuzzy_duplicates(aggregator_job, direct_ats_job) is True

    # When deduplicated, direct ATS job should win over aggregator
    deduped = deduplicate_raw_jobs([aggregator_job, direct_ats_job, different_job])
    assert len(deduped) == 2
    razorpay_result = [j for j in deduped if "razorpay" in j.company.lower()][0]
    assert razorpay_result.source == "greenhouse"
    assert "greenhouse.io" in razorpay_result.apply_url


def test_load_companies_yaml():
    companies = load_companies()
    assert len(companies) >= 40
    names = [c["name"] for c in companies]
    assert "Razorpay" in names
    assert "CRED" in names
    assert "Urban Company" in names
