"""
Pydantic DTOs (Data Transfer Objects) for request / response validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Parsed Resume Schema  (what Gemini MUST return)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None


class CareerPreferences(BaseModel):
    desired_roles: List[str] = Field(default_factory=list)
    desired_locations: List[str] = Field(default_factory=list)
    job_type: Optional[str] = None  # full-time / part-time / internship
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None
    description: Optional[str] = None


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    bullet_points: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    bullet_points: List[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class ResumeMeta(BaseModel):
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    extraction_method: Optional[str] = None
    parsed_at: Optional[str] = None
    confidence: Optional[float] = None


class ParsedResume(BaseModel):
    """Complete structured resume — the LLM output contract."""
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    career_preferences: CareerPreferences = Field(default_factory=CareerPreferences)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    resume_meta: ResumeMeta = Field(default_factory=ResumeMeta)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ATS Score & Tailoring DTOs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ATSScoreRequest(BaseModel):
    profile_json: Dict[str, Any] = Field(..., description="Structured resume JSON (ParsedResume).")
    job_description: str = Field(..., min_length=20, description="Full text of the job description.")


class ATSScoreResponse(BaseModel):
    ats_score: float = Field(..., ge=0, le=100)
    missing_keywords: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    fixes: List[str] = Field(default_factory=list)


class TailorRequest(BaseModel):
    profile_json: Dict[str, Any] = Field(..., description="Structured resume JSON (ParsedResume).")
    job_description: str = Field(..., min_length=20, description="Full text of the job description.")
    strictness: Optional[str] = Field("balanced", description="Tailoring strictness: 'conservative', 'balanced', 'assertive'")


class TailorResponse(BaseModel):
    version_id: uuid.UUID
    tailored_json: Dict[str, Any]
    pdf_path: str
    ats_score: Optional[float] = None
    ats_report: Optional[Dict[str, Any]] = None
    change_log: List[Dict[str, Any]] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    coverage_percent: Optional[float] = None
    fidelity_score: Optional[float] = None


class RecompileRequest(BaseModel):
    bullet_overrides: Dict[str, str] = Field(default_factory=dict, description="Map of bullet_id -> accepted/reverted text")
    strictness: Optional[str] = "balanced"


class JobTailorResponse(BaseModel):
    resume_version_id: uuid.UUID
    download_url: str
    changes_summary: str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Upload Response & API Envelope
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ResumeUploadResponse(BaseModel):
    profile_id: uuid.UUID
    parsed_resume: ParsedResume
    raw_text_length: int
    extraction_method: str


class APIResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  User & Job DTOs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str = Field(..., min_length=20)
    requirements: Optional[str] = None


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str]
    location: Optional[str]
    description: str
    requirements: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class JobDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    apply_url: Optional[str] = None
    created_at: datetime
    
    # Match insights (populated if profile_id is provided)
    match_score: Optional[int] = None
    match_reasons: Optional[List[str]] = None
    model_config = {"from_attributes": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Application Tracking DTOs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ApplicationStatus(str, Enum):
    applied = "applied"
    viewed = "viewed"
    interview = "interview"
    rejected = "rejected"


class ApplicationCreate(BaseModel):
    profile_id: uuid.UUID
    job_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    job_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID]
    status: ApplicationStatus
    notes: Optional[str]
    applied_at: datetime
    updated_at: datetime
    
    # Injected from the Job model for convenience on the frontend
    apply_url: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    model_config = {"from_attributes": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Profile Editing DTOs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProfileUpdateRequest(BaseModel):
    parsed_json: Optional[Dict[str, Any]] = Field(None, description="Full raw parsed profile JSON replacement")
    summary: Optional[str] = Field(None, description="Updates the summary inside personal_info")
    skills: Optional[List[str]] = None
    experience: Optional[List[Experience]] = None
    projects: Optional[List[Project]] = None
    education: Optional[List[Education]] = None