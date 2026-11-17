"""
Application configuration — loaded from .env via pydantic-settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.  All values can be overridden through
    environment variables or a `.env` file placed in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "HireMe AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "sqlite+aiosqlite:///./ai_job_platform.db"
    )

    # ── Authentication & Security ─────────────────────────────────────────
    JWT_SECRET_KEY: str = "hireme-ai-secret-key-prod-super-safe-2026-secure"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str = ""

    # ── AI / LLM Configuration ──────────────────────────────────────────
    LLM_PROVIDER: str = "groq"  # "groq" or "gemini"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    LLM_TIMEOUT: float = 60.0
    LLM_MAX_RETRIES: int = 3

    # ── Job Ingestion Sources & Toggles ──────────────────────────────────
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ENABLE_ADZUNA: bool = True

    JOOBLE_KEY: str = ""
    ENABLE_JOOBLE: bool = True

    RAPIDAPI_KEY: str = ""
    ENABLE_JSEARCH: bool = True

    CAREERJET_AFFID: str = ""
    ENABLE_CAREERJET: bool = True

    ENABLE_GREENHOUSE: bool = True
    ENABLE_LEVER: bool = True
    ENABLE_ASHBY: bool = True
    ENABLE_ARBEITNOW: bool = True
    ENABLE_THEMUSE: bool = True
    ENABLE_HIMALAYAS: bool = True
    ENABLE_REMOTIVE: bool = True

    JOB_INGEST_INTERVAL_HOURS: int = 6
    JOB_MAX_AGE_DAYS: int = 30
    JOB_INACTIVE_DAYS: int = 14

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the JSON-encoded CORS origins string into a Python list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    # ── File Storage ─────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    GENERATED_DIR: str = "./generated"

    def ensure_dirs(self) -> None:
        """Create upload / generated directories if they don't exist."""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.GENERATED_DIR).mkdir(parents=True, exist_ok=True)


# Module-level singleton — import this everywhere.
settings = Settings()
