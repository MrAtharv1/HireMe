"""
Base classes and DTOs for Job Ingestion Sources.
"""

from __future__ import annotations

import abc
import html
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


def clean_html_text(raw_html: Optional[str]) -> str:
    """Strip HTML tags, scripts, styles and unescape entities into clean plain text."""
    if not raw_html:
        return ""
    # Remove script and style tags completely
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block level elements with space
    text = re.sub(r"</?(p|div|br|li|ul|ol|h[1-6]|tr|td|th)[^>]*>", " ", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove spaces before punctuation
    text = re.sub(r"\s+([!?,.:;])", r"\1", text)
    # Normalize whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_valid_http_url(url: Optional[str]) -> bool:
    """Validate that the URL has http or https scheme and a network location."""
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


class RawJob(BaseModel):
    """Normalized job entity produced by all source adapters."""
    title: str = Field(..., min_length=2)
    company: str = Field(..., min_length=1)
    location: str = "Remote"
    remote: bool = False
    description: str = Field(..., min_length=10)
    apply_url: str
    source: str
    source_job_id: str
    posted_at: Optional[datetime] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    employment_type: Optional[str] = None

    @field_validator("apply_url")
    @classmethod
    def validate_apply_url(cls, v: str) -> str:
        clean = v.strip()
        if not is_valid_http_url(clean):
            raise ValueError(f"Invalid apply_url: {v}")
        return clean

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        return clean_html_text(v)


class JobSource(abc.ABC):
    """Abstract interface for all job scraping/API adapters."""

    name: str = "base"

    @abc.abstractmethod
    async def fetch_jobs(self, limit: int = 50) -> List[RawJob]:
        """Fetch raw jobs from external source, returning normalized RawJob objects."""
        pass
