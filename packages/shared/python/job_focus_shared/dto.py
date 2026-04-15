from __future__ import annotations

from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .enums import (
    ApplicationStatus,
    EmploymentType,
    JobSource,
    MatchStrength,
    PacketStatus,
    ReviewAction,
    SourceHealthStatus,
    WorkMode,
)


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class SharedModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class UserProfileDTO(SharedModel):
    id: str
    email: str
    full_name: str
    headline: str
    location: str
    target_roles: list[str]
    years_experience: int
    seniority_level: str | None
    authorization_regions: list[str]
    created_at: datetime


class ProfileUpdateDTO(SharedModel):
    full_name: str
    headline: str
    location: str
    target_roles: list[str]
    years_experience: int
    seniority_level: str | None
    authorization_regions: list[str]


class ResumeDTO(SharedModel):
    id: str
    user_id: str
    version: int
    title: str
    file_name: str
    summary: str
    skills: list[str]
    is_default: bool
    updated_at: datetime


class UserPreferenceDTO(SharedModel):
    id: str
    user_id: str
    preferred_locations: list[str]
    preferred_work_modes: list[WorkMode]
    preferred_employment_types: list[EmploymentType]
    desired_salary_min: int | None
    desired_salary_max: int | None
    auto_apply_enabled: bool
    auto_apply_min_score: int
    updated_at: datetime


class UserPreferenceUpdateDTO(SharedModel):
    preferred_locations: list[str]
    preferred_work_modes: list[WorkMode]
    preferred_employment_types: list[EmploymentType]
    desired_salary_min: int | None
    desired_salary_max: int | None
    auto_apply_enabled: bool
    auto_apply_min_score: int


class JobDTO(SharedModel):
    id: str
    external_job_id: str
    company: str
    title: str
    location: str
    work_mode: WorkMode
    employment_type: EmploymentType
    source: JobSource
    salary_min: int
    salary_max: int
    description: str
    application_url: str | None
    seniority_level: str | None
    authorization_requirement: str | None
    posted_at: datetime


class DiscoveredJobDTO(SharedModel):
    source: JobSource
    external_job_id: str
    company: str
    title: str
    location: str
    work_mode: WorkMode
    employment_type: EmploymentType
    salary_min: int
    salary_max: int
    description: str
    application_url: str | None
    seniority_level: str | None
    authorization_requirement: str | None
    posted_at: datetime
    raw_payload: dict[str, Any]


class MatchDTO(SharedModel):
    id: str
    user_id: str
    job_id: str
    score: int
    strength: MatchStrength
    rationale: str
    why_matched: dict[str, Any]
    created_at: datetime


class ApplicationPacketDTO(SharedModel):
    id: str
    user_id: str
    job_id: str
    resume_id: str | None
    status: PacketStatus
    selected_resume_version: int | None
    tailored_resume_summary: str | None
    cover_note: str | None
    screening_answers: dict[str, str]
    missing_fields: list[str]
    updated_at: datetime


class ApplicationEventDTO(SharedModel):
    id: str
    application_id: str
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    event_type: str
    actor: str
    note: str | None
    payload: dict[str, Any]
    created_at: datetime


class ApplicationDTO(SharedModel):
    id: str
    user_id: str
    job_id: str
    status: ApplicationStatus
    packet_id: str | None
    packet_status: PacketStatus | None
    notes: str
    submitted_at: datetime | None
    last_error: str | None
    blocking_reason: str | None
    latest_error_code: str | None
    confirmation_details: dict[str, Any] | None
    job: JobDTO
    match_score: int | None
    match_strength: MatchStrength | None
    packet: ApplicationPacketDTO | None
    events: list[ApplicationEventDTO]
    created_at: datetime
    updated_at: datetime


class ApplicationReviewRequestDTO(SharedModel):
    action: ReviewAction
    note: str | None = None


class SourceHealthDTO(SharedModel):
    source: JobSource
    display_name: str
    status: SourceHealthStatus
    is_active: bool
    job_count: int
    last_seen_at: datetime | None
    last_posted_at: datetime | None
    note: str


class TrackerOverviewDTO(SharedModel):
    user_count: int
    job_count: int
    match_count: int
    application_count: int
    configured_live_source_count: int
    last_ingest_at: datetime | None
    last_score_at: datetime | None
    last_packet_at: datetime | None
    last_apply_at: datetime | None
    redis_connected: bool


class LoginRequestDTO(SharedModel):
    email: str
    password: str


class AuthSessionDTO(SharedModel):
    access_token: str
    token_type: str
    user: UserProfileDTO


class DashboardSnapshotDTO(SharedModel):
    profile: UserProfileDTO
    preferences: UserPreferenceDTO
    resume: ResumeDTO
    jobs: list[JobDTO]
    matches: list[MatchDTO]
    applications: list[ApplicationDTO]
    source_health: list[SourceHealthDTO]
    tracker: TrackerOverviewDTO
