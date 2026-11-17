"""
Job sources package export and discovery.
"""

from typing import List

from app.core.config import settings
from app.services.job_sources.base import JobSource, RawJob
from app.services.job_sources.remotive import RemotiveJobSource
from app.services.job_sources.adzuna import AdzunaJobSource
from app.services.job_sources.jooble import JoobleJobSource
from app.services.job_sources.jsearch import JSearchJobSource
from app.services.job_sources.careerjet import CareerjetJobSource
from app.services.job_sources.ats_boards import (
    GreenhouseJobSource,
    LeverJobSource,
    AshbyJobSource,
)
from app.services.job_sources.arbeitnow import ArbeitnowJobSource
from app.services.job_sources.themuse import TheMuseJobSource
from app.services.job_sources.himalayas import HimalayasJobSource


def get_enabled_job_sources() -> List[JobSource]:
    """Returns a list of instantiated and enabled JobSource adapters."""
    sources: List[JobSource] = []

    if settings.ENABLE_REMOTIVE:
        sources.append(RemotiveJobSource())
    if settings.ENABLE_ADZUNA:
        sources.append(AdzunaJobSource())
    if settings.ENABLE_JOOBLE:
        sources.append(JoobleJobSource())
    if settings.ENABLE_JSEARCH:
        sources.append(JSearchJobSource())
    if settings.ENABLE_CAREERJET:
        sources.append(CareerjetJobSource())
    if settings.ENABLE_GREENHOUSE:
        sources.append(GreenhouseJobSource())
    if settings.ENABLE_LEVER:
        sources.append(LeverJobSource())
    if settings.ENABLE_ASHBY:
        sources.append(AshbyJobSource())
    if settings.ENABLE_ARBEITNOW:
        sources.append(ArbeitnowJobSource())
    if settings.ENABLE_THEMUSE:
        sources.append(TheMuseJobSource())
    if settings.ENABLE_HIMALAYAS:
        sources.append(HimalayasJobSource())

    return sources
