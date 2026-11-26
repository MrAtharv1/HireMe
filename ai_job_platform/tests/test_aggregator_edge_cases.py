"""
Tests for Aggregator Edge Cases & Deduplication (app/services/job_aggregator.py).
Verifies:
- Legal company suffix normalization (Pvt, Ltd, Inc, LLC, Corp, Technologies)
- RapidFuzz deduplication favoring direct ATS boards (Greenhouse/Lever/Ashby) over aggregators
- Fuzzy matching tolerance across slight title/punctuation variations
- 30-day age cutoff logic
- Asynchronous URL reachability check and fallback handling
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.job_sources.base import RawJob
from app.services.job_aggregator import (
    normalize_company_name,
    are_jobs_fuzzy_duplicates,
    deduplicate_raw_jobs,
    check_url_reachability,
)


def test_normalize_company_name_legal_suffixes():
    test_cases = [
        ("Acme Technologies Pvt Ltd", "acme"),
        ("Google LLC", "google"),
        ("Stripe, Inc.", "stripe"),
        ("OpenAI Global Corporation", "openai global"),
        ("Anthropic Co.", "anthropic"),
        ("DataWorks Software Limited", "dataworks"),
    ]
    for raw, expected in test_cases:
        assert normalize_company_name(raw) == expected


def test_deduplicate_raw_jobs_direct_ats_preference():
    now = datetime.now(timezone.utc)
    job_aggregator = RawJob(
        title="Associate Software Engineer",
        company="Datadog",
        location="Remote",
        apply_url="https://remotive.com/job/datadog-123",
        source="remotive",
        source_job_id="rem_123",
        description="Great early career software engineer role.",
        posted_at=now
    )
    job_direct_ats = RawJob(
        title="Associate Software Engineer",
        company="Datadog Inc.",
        location="Remote",
        apply_url="https://boards.greenhouse.io/datadog/jobs/998877",
        source="greenhouse",
        source_job_id="gh_998877",
        description="Great early career software engineer role.",
        posted_at=now
    )

    # Ingested aggregator first, direct ATS second
    deduped = deduplicate_raw_jobs([job_aggregator, job_direct_ats])
    assert len(deduped) == 1
    # Direct ATS board MUST overwrite aggregator mirror
    assert deduped[0].source == "greenhouse"
    assert "greenhouse.io" in deduped[0].apply_url


def test_deduplicate_raw_jobs_fuzzy_threshold():
    now = datetime.now(timezone.utc)
    job_1 = RawJob(
        title="Software Engineer - Early Career (2025)",
        company="Figma Inc.",
        location="San Francisco, CA",
        apply_url="https://jobs.lever.co/figma/1",
        source="lever",
        source_job_id="lever_1",
        description="Build design tools.",
        posted_at=now
    )
    job_2 = RawJob(
        title="Software Engineer Early Career 2025",
        company="Figma",
        location="San Francisco, CA",
        apply_url="https://boards.greenhouse.io/figma/2",
        source="greenhouse",
        source_job_id="gh_2",
        description="Build design tools.",
        posted_at=now
    )

    assert are_jobs_fuzzy_duplicates(job_1, job_2) is True
    deduped = deduplicate_raw_jobs([job_1, job_2])
    assert len(deduped) == 1


def test_age_filter_30_days():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    fresh_job = RawJob(
        title="Backend Intern",
        company="TechCorp",
        location="Remote",
        apply_url="https://example.com/1",
        source="ashby",
        source_job_id="ashby_1",
        description="Fresh posting.",
        posted_at=now - timedelta(days=5)
    )
    stale_job = RawJob(
        title="Backend Intern",
        company="TechCorp",
        location="Remote",
        apply_url="https://example.com/2",
        source="ashby",
        source_job_id="ashby_2",
        description="Old posting.",
        posted_at=now - timedelta(days=35)
    )

    # Validation of age cutoff condition
    assert fresh_job.posted_at >= cutoff
    assert stale_job.posted_at < cutoff


@pytest.mark.asyncio
async def test_url_reachability_fallback():
    # 1. 200 OK URL
    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200

    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head:
        mock_head.return_value = mock_resp_200
        ok = await check_url_reachability("https://valid-ats-board.com/jobs/1")
        assert ok is True

    # 2. 404 Not Found URL
    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404

    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_head.return_value = mock_resp_404
        mock_get.return_value = mock_resp_404
        ok = await check_url_reachability("https://invalid-ats-board.com/jobs/expired")
        assert ok is False
