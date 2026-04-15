from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Profile, Resume, User, UserPreference
from job_focus_shared import EmploymentType, WorkMode


class PrimaryUserBootstrapInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str
    password: str
    full_name: str
    headline: str
    location: str
    target_roles: list[str] = Field(min_length=1)
    years_experience: int = Field(ge=0)
    seniority_level: str | None = None
    authorization_regions: list[str] = Field(min_length=1)
    preferred_locations: list[str] = Field(min_length=1)
    preferred_work_modes: list[WorkMode] = Field(min_length=1)
    preferred_employment_types: list[EmploymentType] = Field(default_factory=list)
    desired_salary_min: int | None = Field(default=None, ge=0)
    desired_salary_max: int | None = Field(default=None, ge=0)
    auto_apply_enabled: bool = False
    auto_apply_min_score: int = Field(default=85, ge=0, le=100)
    resume_title: str
    resume_file_name: str
    resume_summary: str
    resume_skills: list[str] = Field(min_length=1)
    resume_version: int = Field(default=1, ge=1)

    @field_validator(
        "email",
        "password",
        "full_name",
        "headline",
        "location",
        "resume_title",
        "resume_file_name",
        "resume_summary",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field is required.")
        return value.strip()

    @field_validator(
        "target_roles",
        "authorization_regions",
        "preferred_locations",
        "resume_skills",
        mode="before",
    )
    @classmethod
    def normalize_string_lists(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("A list value is required.")
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if not normalized:
            raise ValueError("At least one value is required.")
        return normalized

    @model_validator(mode="after")
    def validate_salary_range(self) -> "PrimaryUserBootstrapInput":
        if (
            self.desired_salary_min is not None
            and self.desired_salary_max is not None
            and self.desired_salary_min > self.desired_salary_max
        ):
            raise ValueError("desired_salary_min cannot be greater than desired_salary_max.")
        return self


@dataclass(frozen=True, slots=True)
class PrimaryUserBootstrapResult:
    user_id: str
    email: str
    profile_id: str
    preferences_id: str
    resume_id: str


def bootstrap_primary_user(
    session: Session,
    payload: PrimaryUserBootstrapInput,
) -> PrimaryUserBootstrapResult:
    existing_user_count = session.scalar(select(func.count(User.id))) or 0
    if existing_user_count > 0:
        raise RuntimeError(
            "Primary user bootstrap is only allowed when the system has zero users."
        )

    user = User(
        email=payload.email,
        hashed_password=payload.password,
        is_active=True,
    )
    session.add(user)
    session.flush()

    profile = Profile(
        user_id=user.id,
        full_name=payload.full_name,
        headline=payload.headline,
        location=payload.location,
        target_roles=payload.target_roles,
        years_experience=payload.years_experience,
        seniority_level=payload.seniority_level,
        authorization_regions=payload.authorization_regions,
    )
    preferences = UserPreference(
        user_id=user.id,
        preferred_locations=payload.preferred_locations,
        preferred_work_modes=[mode.value for mode in payload.preferred_work_modes],
        preferred_employment_types=[
            employment_type.value for employment_type in payload.preferred_employment_types
        ],
        desired_salary_min=payload.desired_salary_min,
        desired_salary_max=payload.desired_salary_max,
        auto_apply_enabled=payload.auto_apply_enabled,
        auto_apply_min_score=payload.auto_apply_min_score,
    )
    resume = Resume(
        user_id=user.id,
        version=payload.resume_version,
        title=payload.resume_title,
        file_name=payload.resume_file_name,
        summary=payload.resume_summary,
        skills=payload.resume_skills,
        is_default=True,
    )
    session.add_all([profile, preferences, resume])
    session.flush()

    return PrimaryUserBootstrapResult(
        user_id=user.id,
        email=user.email,
        profile_id=profile.id,
        preferences_id=preferences.id,
        resume_id=resume.id,
    )
