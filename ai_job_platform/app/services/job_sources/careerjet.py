"""
Careerjet Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.core.config import settings
from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class CareerjetJobSource(JobSource):
    name = "careerjet"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        if not settings.CAREERJET_AFFID:
            logger.debug("Careerjet affiliate ID not configured. Skipping source.")
            return []

        raw_jobs: List[RawJob] = []
        url = "http://public.api.careerjet.net/search"
        params = {
            "affid": settings.CAREERJET_AFFID,
            "user_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "keywords": "junior software engineer fresher",
            "location": "India",
            "page_size": min(limit, 50),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code != 200:
                    logger.warning("Careerjet returned status %d", res.status_code)
                    return []
                data = res.json()
                jobs = data.get("jobs", [])

                for idx, item in enumerate(jobs):
                    apply_url = item.get("url")
                    if not apply_url:
                        continue

                    raw_jobs.append(
                        RawJob(
                            title=item.get("title", "").strip(),
                            company=item.get("company", "Unknown").strip(),
                            location=item.get("locations", "India"),
                            remote="remote" in (item.get("title", "") + item.get("description", "")).lower(),
                            description=item.get("description", ""),
                            apply_url=apply_url,
                            source="careerjet",
                            source_job_id=str(item.get("id") or f"cj_{idx}_{hash(apply_url)}"),
                            posted_at=datetime.now(timezone.utc),
                            salary_min=None,
                            salary_max=None,
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching Careerjet jobs: %s", e)

        return raw_jobs
