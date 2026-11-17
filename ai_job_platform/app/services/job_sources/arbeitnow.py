"""
Arbeitnow Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class ArbeitnowJobSource(JobSource):
    name = "arbeitnow"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        raw_jobs: List[RawJob] = []
        url = "https://www.arbeitnow.com/api/job-board-api"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                items = data.get("data", [])

                for item in items:
                    apply_url = item.get("url")
                    if not apply_url:
                        continue

                    posted_epoch = item.get("created_at")
                    posted_at = datetime.fromtimestamp(posted_epoch, tz=timezone.utc) if posted_epoch else datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("title", "").strip(),
                            company=item.get("company_name", "Unknown").strip(),
                            location=item.get("location", "Remote"),
                            remote=bool(item.get("remote")),
                            description=item.get("description", ""),
                            apply_url=apply_url,
                            source="arbeitnow",
                            source_job_id=str(item.get("slug")),
                            posted_at=posted_at,
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching Arbeitnow jobs: %s", e)

        return raw_jobs[:limit]
