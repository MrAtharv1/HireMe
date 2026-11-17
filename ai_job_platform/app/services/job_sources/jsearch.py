"""
JSearch via RapidAPI Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.core.config import settings
from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class JSearchJobSource(JobSource):
    name = "jsearch"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        if not settings.RAPIDAPI_KEY:
            logger.debug("RapidAPI key not configured for JSearch. Skipping source.")
            return []

        raw_jobs: List[RawJob] = []
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": "junior software engineer in India",
            "page": "1",
            "num_pages": "1",
            "date_posted": "week",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers, params=params)
                if res.status_code != 200:
                    logger.warning("JSearch returned status %d", res.status_code)
                    return []
                data = res.json()
                items = data.get("data", [])

                for item in items:
                    apply_url = item.get("job_apply_link") or (item.get("apply_options") or [{}])[0].get("apply_link")
                    if not apply_url:
                        continue

                    posted_str = item.get("job_posted_at_datetime_utc")
                    posted_at = None
                    if posted_str:
                        try:
                            posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
                        except Exception:
                            posted_at = datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("job_title", "").strip(),
                            company=item.get("employer_name", "Unknown").strip(),
                            location=f"{item.get('job_city', '')}, {item.get('job_country', '')}".strip(" ,") or "India",
                            remote=bool(item.get("job_is_remote")),
                            description=item.get("job_description", ""),
                            apply_url=apply_url,
                            source="jsearch",
                            source_job_id=str(item.get("job_id")),
                            posted_at=posted_at,
                            salary_min=item.get("job_min_salary"),
                            salary_max=item.get("job_max_salary"),
                            salary_currency=item.get("job_salary_currency"),
                            employment_type=item.get("job_employment_type"),
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching JSearch jobs: %s", e)

        return raw_jobs
