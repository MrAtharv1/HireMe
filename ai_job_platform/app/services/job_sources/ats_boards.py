"""
ATS Job Board Adapters for Greenhouse, Lever, and Ashby.
Reads companies from companies.yaml.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml

from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)

COMPANIES_YAML_PATH = Path(__file__).parent / "companies.yaml"


def load_companies() -> List[Dict[str, str]]:
    """Load company board list from companies.yaml."""
    if not COMPANIES_YAML_PATH.exists():
        logger.warning("companies.yaml not found at %s", COMPANIES_YAML_PATH)
        return []
    try:
        with open(COMPANIES_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("companies", [])
    except Exception as e:
        logger.error("Failed to parse companies.yaml: %s", e)
        return []


class GreenhouseJobSource(JobSource):
    name = "greenhouse"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        companies = [c for c in load_companies() if c.get("ats") == "greenhouse"]
        raw_jobs: List[RawJob] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for comp in companies:
                slug = comp.get("slug")
                name = comp.get("name", slug)
                if not slug:
                    continue
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                try:
                    res = await client.get(url)
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    jobs = data.get("jobs", [])
                    for item in jobs:
                        apply_url = item.get("absolute_url")
                        if not apply_url:
                            continue

                        location = item.get("location", {}).get("name", "India")
                        raw_jobs.append(
                            RawJob(
                                title=item.get("title", "").strip(),
                                company=name,
                                location=location,
                                remote="remote" in (location + item.get("title", "")).lower(),
                                description=f"{item.get('title')} at {name}. Location: {location}.",
                                apply_url=apply_url,
                                source="greenhouse",
                                source_job_id=f"{slug}_{item.get('id')}",
                                posted_at=datetime.now(timezone.utc),
                            )
                        )
                except Exception as e:
                    logger.debug("Error fetching Greenhouse board %s: %s", slug, e)

        return raw_jobs[:limit]


class LeverJobSource(JobSource):
    name = "lever"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        companies = [c for c in load_companies() if c.get("ats") == "lever"]
        raw_jobs: List[RawJob] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for comp in companies:
                slug = comp.get("slug")
                name = comp.get("name", slug)
                if not slug:
                    continue
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                try:
                    res = await client.get(url)
                    if res.status_code != 200:
                        continue
                    jobs = res.json()
                    if not isinstance(jobs, list):
                        continue

                    for item in jobs:
                        apply_url = item.get("applyUrl") or item.get("hostedUrl")
                        if not apply_url:
                            continue

                        cats = item.get("categories", {})
                        location = cats.get("location", "India")
                        desc = item.get("descriptionPlain") or item.get("text", "")
                        raw_jobs.append(
                            RawJob(
                                title=item.get("text", "").strip(),
                                company=name,
                                location=location,
                                remote="remote" in (location + item.get("text", "")).lower(),
                                description=desc,
                                apply_url=apply_url,
                                source="lever",
                                source_job_id=f"{slug}_{item.get('id')}",
                                posted_at=datetime.now(timezone.utc),
                                employment_type=cats.get("commitment"),
                            )
                        )
                except Exception as e:
                    logger.debug("Error fetching Lever board %s: %s", slug, e)

        return raw_jobs[:limit]


class AshbyJobSource(JobSource):
    name = "ashby"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        companies = [c for c in load_companies() if c.get("ats") == "ashby"]
        raw_jobs: List[RawJob] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for comp in companies:
                slug = comp.get("slug")
                name = comp.get("name", slug)
                if not slug:
                    continue
                url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                try:
                    res = await client.get(url)
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    jobs = data.get("jobs", [])
                    for item in jobs:
                        apply_url = item.get("applyUrl") or item.get("jobUrl")
                        if not apply_url:
                            continue

                        location = item.get("location", "Remote")
                        raw_jobs.append(
                            RawJob(
                                title=item.get("title", "").strip(),
                                company=name,
                                location=location,
                                remote=bool(item.get("isRemote")),
                                description=f"{item.get('title')} at {name}. Location: {location}.",
                                apply_url=apply_url,
                                source="ashby",
                                source_job_id=f"{slug}_{item.get('id')}",
                                posted_at=datetime.now(timezone.utc),
                                employment_type=item.get("employmentType"),
                            )
                        )
                except Exception as e:
                    logger.debug("Error fetching Ashby board %s: %s", slug, e)

        return raw_jobs[:limit]
