"""
Async SQLAlchemy ORM models.

Tables
------
- users           — registered platform users
- profiles        — parsed resume JSON for a user
- jobs            — job listings with descriptions (now with categories)
- matches         — ATS score results (profile ↔ job)
- resume_versions — tailored resume snapshots + generated PDF path
- applications    — tracks jobs a user has applied to
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Portable JSON type: uses JSONB on PostgreSQL, standard JSON on SQLite
PortableJSON = JSON().with_variant(JSONB, "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# Application Status Enum for the database
class ApplicationStatusEnum(str, enum.Enum):
    applied = "applied"
    viewed = "viewed"
    interview = "interview"
    rejected = "rejected"


# ─────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")  # "email" | "google"
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    profiles: Mapped[List["Profile"]] = relationship(back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    resume_versions: Mapped[List["ResumeVersion"]] = relationship(back_populates="user", cascade="all, delete-orphan", lazy="selectin")


# ─────────────────────────────────────────────────────────────────────────
# Profile  — stores the full parsed resume JSON
# ─────────────────────────────────────────────────────────────────────────
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_filename: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[Optional[dict]] = mapped_column(PortableJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profiles")
    matches: Mapped[List["Match"]] = relationship(back_populates="profile", cascade="all, delete-orphan", lazy="selectin")


# ─────────────────────────────────────────────────────────────────────────
# Job  — job listings / descriptions
# ─────────────────────────────────────────────────────────────────────────
class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uq_jobs_source_source_job_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="unknown", index=True, nullable=False)
    source_job_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    company: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) 
    apply_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    apply_url_ok: Mapped[bool] = mapped_column(Boolean, default=True)

    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    seniority_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # intern, entry, junior, etc.
    min_years_exp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_years_exp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fresher_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    skills_required: Mapped[Optional[dict]] = mapped_column(PortableJSON, nullable=True)

    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    matches: Mapped[List["Match"]] = relationship(back_populates="job", cascade="all, delete-orphan", lazy="selectin")


# ─────────────────────────────────────────────────────────────────────────
# Match  — ATS scoring result (Profile × Job)
# ─────────────────────────────────────────────────────────────────────────
class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    ats_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    missing_keywords: Mapped[Optional[list]] = mapped_column(PortableJSON, nullable=True)
    strengths: Mapped[Optional[list]] = mapped_column(PortableJSON, nullable=True)
    fixes: Mapped[Optional[list]] = mapped_column(PortableJSON, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="matches")
    job: Mapped["Job"] = relationship(back_populates="matches")


# ─────────────────────────────────────────────────────────────────────────
# ResumeVersion  — tailored resume snapshot + generated PDF path
# ─────────────────────────────────────────────────────────────────────────
class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    tailored_json: Mapped[Optional[dict]] = mapped_column(PortableJSON, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tex_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tex_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ats_report: Mapped[Optional[dict]] = mapped_column(PortableJSON, nullable=True)
    version_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resume_versions")
    job: Mapped[Optional["Job"]] = relationship(lazy="selectin")


# ─────────────────────────────────────────────────────────────────────────
# Application — tracks jobs a user has applied to
# ─────────────────────────────────────────────────────────────────────────
class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[str] = mapped_column(SQLEnum(ApplicationStatusEnum, native_enum=False), default=ApplicationStatusEnum.applied, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    profile: Mapped["Profile"] = relationship(lazy="selectin")
    job: Mapped["Job"] = relationship(lazy="selectin")
    resume_version: Mapped[Optional["ResumeVersion"]] = relationship(lazy="selectin")