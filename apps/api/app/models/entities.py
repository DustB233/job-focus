from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from job_focus_shared import (
    ApplicationStatus,
    EmploymentType,
    JobSource,
    MatchStrength,
    PacketStatus,
    WorkMode,
)
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def enum_values(enum_type: type) -> list[str]:
    return [member.value for member in enum_type]


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False)
    resumes: Mapped[list["Resume"]] = relationship(back_populates="user")
    job_matches: Mapped[list["JobMatch"]] = relationship(back_populates="user")
    application_packets: Mapped[list["ApplicationPacket"]] = relationship(back_populates="user")
    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    auth_sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user")
    user_preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user", uselist=False
    )


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    headline: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    seniority_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authorization_regions: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="profile")


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("user_id", "version", name="uq_resumes_user_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="resumes")
    application_packets: Mapped[list["ApplicationPacket"]] = relationship(back_populates="resume")


class JobSourceConfig(TimestampMixin, Base):
    __tablename__ = "job_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[JobSource] = mapped_column(
        Enum(JobSource, native_enum=False, values_callable=enum_values),
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    jobs: Mapped[list["Job"]] = relationship(back_populates="job_source")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("job_source_id", "external_job_id", name="uq_jobs_source_external_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_source_id: Mapped[str] = mapped_column(ForeignKey("job_sources.id"), index=True)
    external_job_id: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode, native_enum=False, values_callable=enum_values)
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, native_enum=False, values_callable=enum_values)
    )
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    application_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authorization_requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    job_source: Mapped[JobSourceConfig] = relationship(back_populates="jobs")
    job_matches: Mapped[list["JobMatch"]] = relationship(back_populates="job")
    application_packets: Mapped[list["ApplicationPacket"]] = relationship(back_populates="job")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")


class JobMatch(TimestampMixin, Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_matches_user_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    match_score: Mapped[int] = mapped_column(Integer)
    strength: Mapped[MatchStrength] = mapped_column(
        Enum(MatchStrength, native_enum=False, values_callable=enum_values)
    )
    rationale: Mapped[str] = mapped_column(Text)
    why_matched: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="job_matches")
    job: Mapped[Job] = relationship(back_populates="job_matches")


class ApplicationPacket(TimestampMixin, Base):
    __tablename__ = "application_packets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    status: Mapped[PacketStatus] = mapped_column(
        Enum(PacketStatus, native_enum=False, values_callable=enum_values)
    )
    selected_resume_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tailored_resume_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    screening_answers: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="application_packets")
    job: Mapped[Job] = relationship(back_populates="application_packets")
    resume: Mapped[Resume | None] = relationship(back_populates="application_packets")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="current_packet",
        foreign_keys="Application.current_packet_id",
    )


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    current_packet_id: Mapped[str | None] = mapped_column(
        ForeignKey("application_packets.id"), nullable=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, values_callable=enum_values)
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_of_application_id: Mapped[str | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    current_packet: Mapped[ApplicationPacket | None] = relationship(
        back_populates="applications", foreign_keys=[current_packet_id]
    )
    events: Mapped[list["ApplicationEvent"]] = relationship(back_populates="application")
    duplicate_of_application: Mapped["Application | None"] = relationship(
        remote_side="Application.id"
    )


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, values_callable=enum_values),
        nullable=True,
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, values_callable=enum_values)
    )
    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(64), default="system")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    application: Mapped[Application] = relationship(back_populates="events")


class AuthSession(TimestampMixin, Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="auth_sessions")


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_work_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_employment_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    desired_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_apply_min_score: Mapped[int] = mapped_column(Integer, default=85)

    user: Mapped[User] = relationship(back_populates="user_preferences")
