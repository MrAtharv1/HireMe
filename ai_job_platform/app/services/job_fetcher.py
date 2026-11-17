"""
Job Ingestion Service — Fetches remote jobs from the Remotive API across multiple categories.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Job

logger = logging.getLogger(__name__)

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"

# The target categories to fetch
CATEGORIES = [
    "software-dev",
    "customer-support",
    "qa",
    "data",
    "devops"
]


async def fetch_and_store_jobs(db: AsyncSession, limit: int = 50) -> Dict[str, Any]:
    """
    Fetch jobs from Remotive API across multiple categories and store them.
    Skips duplicates based on external_id using bulk querying for batch insert efficiency.
    """
    logger.info("Fetching jobs from Remotive API across %d categories...", len(CATEGORIES))
    
    all_fetched_jobs: List[Dict[str, Any]] = []
    
    # 1. Fetch from all categories
    async with httpx.AsyncClient() as client:
        for category in CATEGORIES:
            try:
                # Limit applies per category request
                response = await client.get(f"{REMOTIVE_API_URL}?category={category}&limit={limit}")
                response.raise_for_status()
                data = response.json()
                
                jobs_data = data.get("jobs", [])
                
                # Tag the raw data with our tracked category before flattening the list
                for job in jobs_data:
                    job["_app_category"] = category
                    
                all_fetched_jobs.extend(jobs_data)
                
            except Exception as exc:
                logger.error("Failed to fetch jobs for category %s: %s", category, exc)

    if not all_fetched_jobs:
        return {"success": True, "message": "No jobs found across requested categories.", "added": 0}

    # 2. Extract external IDs and find existing duplicates in a single query
    fetched_external_ids = {str(item.get("id")) for item in all_fetched_jobs if item.get("id")}
    
    existing_query = await db.execute(
        select(Job.external_id).where(Job.external_id.in_(fetched_external_ids))
    )
    existing_ids = set(existing_query.scalars().all())

    # 3. Filter and prepare objects for batch insertion
    new_jobs = []
    processed_ids = set() # To handle duplicate IDs within the API response itself
    
    for item in all_fetched_jobs:
        external_id = str(item.get("id"))
        
        # Skip if it's already in the DB or we already processed it in this batch
        if external_id in existing_ids or external_id in processed_ids:
            continue
            
        processed_ids.add(external_id)

        pub_date_str = item.get("publication_date")
        posted_at = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00")) if pub_date_str else datetime.now(timezone.utc)

        new_job = Job(
            external_id=external_id,
            source="remotive",
            title=item.get("title", "Unknown Title"),
            company=item.get("company_name", "Unknown Company"),
            location=item.get("candidate_required_location", "Worldwide"),
            remote=True,
            description=item.get("description", ""),
            requirements=item.get("category", ""), 
            category=item.get("_app_category", ""),
            apply_url=item.get("url", ""), 
            is_active=True,
            created_at=posted_at,
        )
        new_jobs.append(new_job)

    # 4. Batch Insert
    if new_jobs:
        db.add_all(new_jobs)
        await db.commit()

    added_count = len(new_jobs)
    skipped_count = len(all_fetched_jobs) - added_count
    
    logger.info("Ingestion complete. Added: %d, Skipped: %d", added_count, skipped_count)
    
    return {
        "success": True,
        "message": f"Ingestion complete across {len(CATEGORIES)} categories.",
        "added": added_count,
        "skipped": skipped_count
    }