"""
Himalayas Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class HimalayasJobSource(JobSource):
    name = "himalayas"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        raw_jobs: List[RawJob] = []
        url = "https://himalayas.app/jobs/api"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params={"limit": min(limit, 50)})
                if res.status_code != 200:
                    return []
                data = res.json()
                items = data.get("jobs", [])

                for item in items:
                    apply_url = item.get("applicationUrl") or item.get("applyUrl") or item.get("url")
                    if not apply_url:
                        continue

                    posted_epoch = item.get("pubDate")
                    posted_at = datetime.fromtimestamp(posted_epoch, tz=timezone.utc) if posted_epoch else datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("title", "").strip(),
                            company=item.get("companyName", "Unknown").strip(),
                            location="Remote",
                            remote=True,
                            description=item.get("description", ""),
                            apply_url=apply_url,
                            source="himalayas",
                            source_job_id=str(item.get("id") or item.get("slug")),
                            posted_at=posted_at,
                            salary_min=item.get("minSalary"),
                            salary_max=item.get("maxSalary"),
                            salary_currency=item.get("currency"),
                            employment_type=item.get("employmentType"),
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching Himalayas jobs: %s", e)

        return raw_jobs[:limit]
