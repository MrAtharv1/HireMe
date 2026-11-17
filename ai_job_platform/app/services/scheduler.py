"""
APScheduler configuration for automated periodic job ingestion.
Runs every 6 hours in the background.
"""

from __future__ import annotations

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import async_session_factory
from app.services.job_aggregator import ingest_jobs_pipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_job_ingestion():
    """Periodic task executed by scheduler."""
    logger.info("Executing scheduled job ingestion...")
    try:
        async with async_session_factory() as session:
            result = await ingest_jobs_pipeline(session, limit_per_source=30)
            logger.info("Scheduled ingestion result: %s", result)
    except Exception as exc:
        logger.error("Error in scheduled ingestion task: %s", exc)


def start_scheduler():
    """Starts the APScheduler background thread."""
    if not scheduler.running:
        scheduler.add_job(
            scheduled_job_ingestion,
            "interval",
            hours=settings.JOB_INGEST_INTERVAL_HOURS,
            id="job_ingest_periodic",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started (interval: every %d hours).", settings.JOB_INGEST_INTERVAL_HOURS)


def stop_scheduler():
    """Gracefully shuts down APScheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
