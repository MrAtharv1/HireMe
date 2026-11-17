"""
Jooble Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.core.config import settings
from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class JoobleJobSource(JobSource):
    name = "jooble"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        if not settings.JOOBLE_KEY:
            logger.debug("Jooble API key not configured. Skipping source.")
            return []

        raw_jobs: List[RawJob] = []
        url = f"https://jooble.org/api/{settings.JOOBLE_KEY}"
        payload = {
            "keywords": "junior software developer fresher",
            "location": "India",
            "page": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.warning("Jooble returned status %d", res.status_code)
                    return []
                data = res.json()
                jobs = data.get("jobs", [])

                for item in jobs:
                    apply_url = item.get("link")
                    if not apply_url:
                        continue

                    posted_str = item.get("updated")
                    posted_at = None
                    if posted_str:
                        try:
                            posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
                        except Exception:
                            posted_at = datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("title", "").strip(),
                            company=item.get("company", "Unknown").strip(),
                            location=item.get("location", "India"),
                            remote="remote" in (item.get("title", "") + item.get("snippet", "")).lower(),
                            description=item.get("snippet", ""),
                            apply_url=apply_url,
                            source="jooble",
                            source_job_id=str(item.get("id")),
                            posted_at=posted_at,
                            employment_type=item.get("type"),
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching Jooble jobs: %s", e)

        return raw_jobs
