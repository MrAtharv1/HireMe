"""
Adzuna Job Source Adapter (India endpoint).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.core.config import settings
from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class AdzunaJobSource(JobSource):
    name = "adzuna"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
            logger.debug("Adzuna API keys not configured. Skipping source.")
            return []

        raw_jobs: List[RawJob] = []
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_APP_KEY,
            "results_per_page": min(limit, 50),
            "what": "junior software engineer fresher",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code != 200:
                    logger.warning("Adzuna returned status %d", res.status_code)
                    return []
                data = res.json()
                results = data.get("results", [])

                for item in results:
                    apply_url = item.get("redirect_url")
                    if not apply_url:
                        continue

                    posted_str = item.get("created")
                    posted_at = None
                    if posted_str:
                        try:
                            posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
                        except Exception:
                            posted_at = datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("title", "").strip(),
                            company=item.get("company", {}).get("display_name", "Unknown").strip(),
                            location=item.get("location", {}).get("display_name", "India"),
                            remote="remote" in (item.get("title", "") + item.get("description", "")).lower(),
                            description=item.get("description", ""),
                            apply_url=apply_url,
                            source="adzuna",
                            source_job_id=str(item.get("id")),
                            posted_at=posted_at,
                            salary_min=item.get("salary_min"),
                            salary_max=item.get("salary_max"),
                            salary_currency="INR",
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching Adzuna jobs: %s", e)

        return raw_jobs
