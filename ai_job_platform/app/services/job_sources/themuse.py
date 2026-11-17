"""
The Muse Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class TheMuseJobSource(JobSource):
    name = "themuse"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        raw_jobs: List[RawJob] = []
        url = "https://www.themuse.com/api/public/jobs?category=Software%20Engineering&page=1"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return []
                data = res.json()
                items = data.get("results", [])

                for item in items:
                    apply_url = item.get("refs", {}).get("landing_page")
                    if not apply_url:
                        continue

                    locations = item.get("locations", [])
                    loc_name = locations[0].get("name") if locations else "Remote"

                    posted_str = item.get("publication_date")
                    posted_at = None
                    if posted_str:
                        try:
                            posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
                        except Exception:
                            posted_at = datetime.now(timezone.utc)

                    raw_jobs.append(
                        RawJob(
                            title=item.get("name", "").strip(),
                            company=item.get("company", {}).get("name", "Unknown").strip(),
                            location=loc_name,
                            remote="remote" in (loc_name + item.get("name", "")).lower(),
                            description=item.get("contents", ""),
                            apply_url=apply_url,
                            source="themuse",
                            source_job_id=str(item.get("id")),
                            posted_at=posted_at,
                        )
                    )
        except Exception as e:
            logger.warning("Error fetching The Muse jobs: %s", e)

        return raw_jobs[:limit]
