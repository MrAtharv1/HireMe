"""
Remotive Job Source Adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from app.services.job_sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
CATEGORIES = ["software-dev", "data", "qa", "devops", "customer-support"]


class RemotiveJobSource(JobSource):
    name = "remotive"

    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        raw_jobs: List[RawJob] = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for cat in CATEGORIES:
                try:
                    url = f"{REMOTIVE_API_URL}?category={cat}&limit={max(limit // len(CATEGORIES), 10)}"
                    res = await client.get(url)
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    jobs_data = data.get("jobs", [])
                    for item in jobs_data:
                        apply_url = item.get("url")
                        if not apply_url:
                            continue
                        
                        posted_str = item.get("publication_date")
                        posted_at = None
                        if posted_str:
                            try:
                                posted_at = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
                            except Exception:
                                posted_at = datetime.now(timezone.utc)

                        raw_jobs.append(
                            RawJob(
                                title=item.get("title", "").strip(),
                                company=item.get("company_name", "Unknown").strip(),
                                location=item.get("candidate_required_location", "Remote").strip() or "Remote",
                                remote=True,
                                description=item.get("description", ""),
                                apply_url=apply_url,
                                source="remotive",
                                source_job_id=str(item.get("id")),
                                posted_at=posted_at,
                                employment_type=item.get("job_type"),
                            )
                        )
                except Exception as e:
                    logger.warning("Error fetching Remotive category %s: %s", cat, e)
        return raw_jobs
