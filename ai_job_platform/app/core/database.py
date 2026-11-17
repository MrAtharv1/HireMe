"""
Async SQLAlchemy engine, session factory, and FastAPI dependency.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ───────────────────────────────────────────────────────────────
_engine_kwargs = {"echo": settings.DEBUG}
if "sqlite" in settings.DATABASE_URL:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# ── Session Factory ──────────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── FastAPI Dependency ───────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async DB session; auto-commits on success, rolls back on error.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Lifecycle Helpers ────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables that don't yet exist and auto-migrate missing columns."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Auto-migrate missing columns for SQLite
        if "sqlite" in settings.DATABASE_URL:
            def _migrate_sqlite(sync_conn):
                # jobs table migration
                res_jobs = sync_conn.exec_driver_sql("PRAGMA table_info(jobs)").fetchall()
                existing_jobs = {row[1] for row in res_jobs}
                jobs_cols = [
                    ("source_job_id", "VARCHAR(255)"),
                    ("posted_at", "DATETIME"),
                    ("seniority_level", "VARCHAR(50)"),
                    ("min_years_exp", "INTEGER"),
                    ("max_years_exp", "INTEGER"),
                    ("fresher_score", "FLOAT DEFAULT 0.0"),
                    ("skills_required", "TEXT"),
                    ("apply_url_ok", "BOOLEAN DEFAULT 1"),
                    ("salary_min", "FLOAT"),
                    ("salary_max", "FLOAT"),
                    ("salary_currency", "VARCHAR(10)"),
                    ("employment_type", "VARCHAR(50)"),
                    ("last_seen_at", "DATETIME"),
                ]
                for c, t in jobs_cols:
                    if c not in existing_jobs:
                        sync_conn.exec_driver_sql(f"ALTER TABLE jobs ADD COLUMN {c} {t}")

                # resume_versions table migration
                res_rv = sync_conn.exec_driver_sql("PRAGMA table_info(resume_versions)").fetchall()
                existing_rv = {row[1] for row in res_rv}
                rv_cols = [
                    ("tex_path", "VARCHAR(1024)"),
                    ("tex_content", "TEXT"),
                    ("ats_score", "FLOAT"),
                    ("ats_report", "TEXT"),
                ]
                for c, t in rv_cols:
                    if c not in existing_rv:
                        sync_conn.exec_driver_sql(f"ALTER TABLE resume_versions ADD COLUMN {c} {t}")

                # users table migration
                res_u = sync_conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
                existing_u = {row[1] for row in res_u}
                u_cols = [
                    ("auth_provider", "VARCHAR(50) DEFAULT 'email'"),
                    ("google_sub", "VARCHAR(255)"),
                    ("avatar_url", "VARCHAR(1024)"),
                ]
                for c, t in u_cols:
                    if c not in existing_u:
                        sync_conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {c} {t}")

            await conn.run_sync(_migrate_sqlite)


async def close_db() -> None:
    """Dispose of the connection pool."""
    await engine.dispose()
