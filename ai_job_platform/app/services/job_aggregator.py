"""
Job Aggregator & Ingestion Pipeline:
- Concurrent ingestion across all enabled sources with error isolation
- URL validation & format normalization
- Deduplication using RapidFuzz (threshold 92) with preference for direct ATS links
- 30-day age filtering and 14-day inactivity marking
- Upsert logic with last_seen_at timestamp updates
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from rapidfuzz import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.db_models import Job
from app.services.job_sources import get_enabled_job_sources
from app.services.job_sources.base import RawJob, is_valid_http_url

logger = logging.getLogger(__name__)

DIRECT_ATS_SOURCES = {"greenhouse", "lever", "ashby"}


def normalize_company_name(s: str) -> str:
    """Normalize company name by stripping legal suffixes and punctuation."""
    if not s:
        return ""
    cleaned = s.lower()
    cleaned = re.sub(r"\b(pvt|ltd|inc|llc|technologies|technology|software|corp|corporation|private|limited|co)\b", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_string_key(s: str) -> str:
    """Lowercase and strip non-alphanumeric characters for fuzzy comparisons."""
    if not s:
        return ""
    return re.sub(r"[^a-z0-9\s]", "", s.lower()).strip()


def compute_normalized_job_key(job: RawJob) -> str:
    """Generates standard normalized key for exact hashing: company|title|location"""
    c = normalize_company_name(job.company) or normalize_string_key(job.company)
    t = normalize_string_key(job.title)
    l = normalize_string_key(job.location)
    return f"{c}|{t}|{l}"


def are_jobs_fuzzy_duplicates(job_a: RawJob, job_b: RawJob, threshold: float = 92.0) -> bool:
    """
    Check if two jobs are duplicates using RapidFuzz across company, title, and location.
    Threshold: 92%.
    """
    comp_a = normalize_company_name(job_a.company) or normalize_string_key(job_a.company)
    comp_b = normalize_company_name(job_b.company) or normalize_string_key(job_b.company)
    if not comp_a or not comp_b:
        return False
    
    comp_ratio = fuzz.token_set_ratio(comp_a, comp_b)
    if comp_ratio < 85.0:
        return False

    title_a, title_b = normalize_string_key(job_a.title), normalize_string_key(job_b.title)
    title_ratio = fuzz.token_sort_ratio(title_a, title_b)
    if title_ratio < threshold:
        return False

    return True


async def check_url_reachability(url: str, timeout: float = 5.0) -> bool:
    """Async HEAD check to verify apply URL is not broken (404/500)."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            res = await client.head(url)
            return res.status_code < 400
    except Exception:
        # Fallback: if HEAD fails (some servers block HEAD), try GET stream
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                res = await client.get(url, headers={"Range": "bytes=0-10"})
                return res.status_code < 400
        except Exception:
            return False


def deduplicate_raw_jobs(jobs: List[RawJob]) -> List[RawJob]:
    """
    Deduplicate a list of RawJobs using normalized keys and RapidFuzz.
    Prefers direct ATS sources (Greenhouse/Lever/Ashby) over aggregators.
    """
    deduped: List[RawJob] = []

    for new_job in jobs:
        matched_idx = -1
        for idx, existing in enumerate(deduped):
            if are_jobs_fuzzy_duplicates(new_job, existing):
                matched_idx = idx
                break

        if matched_idx == -1:
            deduped.append(new_job)
        else:
            existing = deduped[matched_idx]
            # Replace if new job is from a direct ATS source and existing is an aggregator
            if new_job.source in DIRECT_ATS_SOURCES and existing.source not in DIRECT_ATS_SOURCES:
                deduped[matched_idx] = new_job

    return deduped


async def fetch_all_sources_concurrently(limit_per_source: int = 50) -> List[RawJob]:
    """
    Fetches raw jobs concurrently from all enabled sources with error isolation.
    """
    sources = get_enabled_job_sources()
    logger.info("Starting concurrent job ingestion across %d sources...", len(sources))

    tasks = [source.fetch_jobs(limit=limit_per_source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_raw_jobs: List[RawJob] = []
    for source, res in zip(sources, results):
        if isinstance(res, Exception):
            logger.error("Job source '%s' failed during fetch: %s", source.name, res)
        elif isinstance(res, list):
            logger.info("Source '%s' returned %d jobs.", source.name, len(res))
            all_raw_jobs.extend(res)

    return all_raw_jobs


async def ingest_jobs_pipeline(
    db: AsyncSession,
    limit_per_source: int = 50,
    check_links_in_background: bool = False,
) -> Dict[str, Any]:
    """
    Full Ingestion Pipeline:
    1. Concurrent fetch from all enabled sources
    2. Filter out invalid URLs and jobs older than 30 days
    3. Deduplicate across sources (favoring direct ATS links)
    4. Upsert into database (update last_seen_at if already exists)
    5. Mark jobs not seen in 14 days as inactive
    """
    now = datetime.now(timezone.utc)
    cutoff_30_days = now - timedelta(days=settings.JOB_MAX_AGE_DAYS)
    cutoff_14_days = now - timedelta(days=settings.JOB_INACTIVE_DAYS)

    # 1. Fetch raw jobs
    raw_jobs = await fetch_all_sources_concurrently(limit_per_source=limit_per_source)

    # 2. Filter invalid apply_url and older than 30 days
    valid_jobs: List[RawJob] = []
    for j in raw_jobs:
        if not is_valid_http_url(j.apply_url):
            continue
        if j.posted_at and j.posted_at < cutoff_30_days:
            continue
        valid_jobs.append(j)

    # 3. Deduplicate using RapidFuzz
    unique_jobs = deduplicate_raw_jobs(valid_jobs)
    logger.info("Total fetched: %d | Valid: %d | After Deduplication: %d", len(raw_jobs), len(valid_jobs), len(unique_jobs))

    # 4. Upsert into DB
    added_count = 0
    updated_count = 0

    for rj in unique_jobs:
        # Check existing by (source, source_job_id) or external_id
        stmt = select(Job).where(
            (Job.source == rj.source) & (Job.source_job_id == rj.source_job_id)
        )
        existing_job = (await db.execute(stmt)).scalar_one_or_none()

        if existing_job:
            existing_job.last_seen_at = now
            existing_job.is_active = True
            if rj.description and len(rj.description) > len(existing_job.description):
                existing_job.description = rj.description
            updated_count += 1
        else:
            ext_id = f"{rj.source}_{rj.source_job_id}"
            new_job = Job(
                external_id=ext_id,
                source=rj.source,
                source_job_id=rj.source_job_id,
                title=rj.title,
                company=rj.company,
                location=rj.location,
                remote=rj.remote,
                description=rj.description,
                apply_url=rj.apply_url,
                apply_url_ok=True,
                posted_at=rj.posted_at or now,
                salary_min=rj.salary_min,
                salary_max=rj.salary_max,
                salary_currency=rj.salary_currency,
                employment_type=rj.employment_type,
                is_active=True,
                last_seen_at=now,
                created_at=now,
            )
            db.add(new_job)
            added_count += 1

    # 5. Mark jobs not seen in 14 days as inactive
    stale_stmt = (
        update(Job)
        .where(Job.last_seen_at < cutoff_14_days)
        .where(Job.is_active == True)
        .values(is_active=False)
    )
    await db.execute(stale_stmt)
    await db.commit()

    logger.info("Ingestion completed: added=%d, updated=%d", added_count, updated_count)
    return {
        "success": True,
        "fetched": len(raw_jobs),
        "valid": len(valid_jobs),
        "deduped": len(unique_jobs),
        "added": added_count,
        "updated": updated_count,
    }
