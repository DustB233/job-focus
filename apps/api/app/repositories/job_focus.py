from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from job_focus_shared import (
    ApplicationDTO,
    ApplicationEventDTO,
    ApplicationPacketDTO,
    ApplicationStatus,
    EmploymentType,
    AuthSessionDTO,
    DiscoveredJobDTO,
    JobDTO,
    JobSource,
    LoginRequestDTO,
    MatchDTO,
    PacketStatus,
    ProfileUpdateDTO,
    ResumeDTO,
    SourceCreateDTO,
    SourceHealthDTO,
    SourceHealthStatus,
    SourceRegistryDTO,
    UserPreferenceDTO,
    UserPreferenceUpdateDTO,
    UserProfileDTO,
    WorkMode,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Application,
    ApplicationEvent,
    ApplicationPacket,
    AuthSession,
    Job,
    JobMatch,
    JobSourceConfig,
    Profile,
    Resume,
    User,
    UserPreference,
)

ALLOWED_APPLICATION_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: {
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.SHORTLISTED: {
        ApplicationStatus.DRAFT_READY,
        ApplicationStatus.NEEDS_USER_INPUT,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.DRAFT_READY: {
        ApplicationStatus.NEEDS_USER_INPUT,
        ApplicationStatus.WAITING_REVIEW,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.NEEDS_USER_INPUT: {
        ApplicationStatus.DRAFT_READY,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.WAITING_REVIEW: {
        ApplicationStatus.SUBMITTING,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.SUBMITTING: {
        ApplicationStatus.WAITING_REVIEW,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.FAILED,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.SUBMITTED: set(),
    ApplicationStatus.FAILED: {
        ApplicationStatus.SUBMITTING,
        ApplicationStatus.BLOCKED,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.BLOCKED: {
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.NEEDS_USER_INPUT,
        ApplicationStatus.WAITING_REVIEW,
        ApplicationStatus.DUPLICATE,
    },
    ApplicationStatus.DUPLICATE: set(),
}

AUTOMATED_SOURCE_SLUGS = {JobSource.GREENHOUSE, JobSource.LEVER}
MANUAL_ONLY_SOURCE_SLUGS = {JobSource.MANUAL}


@dataclass(frozen=True, slots=True)
class SourceJobStats:
    job_count: int = 0
    last_seen_at: datetime | None = None
    last_posted_at: datetime | None = None


def _title_case_identifier(value: str) -> str:
    parts = [part for part in value.replace("_", "-").split("-") if part]
    return " ".join(part.title() for part in parts)


def default_source_display_name(slug: JobSource, external_identifier: str | None = None) -> str:
    provider_name = {
        JobSource.GREENHOUSE: "Greenhouse",
        JobSource.LEVER: "Lever",
        JobSource.ASHBY: "Ashby",
        JobSource.MANUAL: "Manual Link",
    }[slug]
    if external_identifier:
        return f"{provider_name} / {_title_case_identifier(external_identifier)}"
    return provider_name


def default_source_base_url(slug: JobSource, external_identifier: str | None = None) -> str | None:
    if slug == JobSource.GREENHOUSE and external_identifier:
        return f"https://boards-api.greenhouse.io/v1/boards/{quote(external_identifier, safe='')}"
    if slug == JobSource.LEVER and external_identifier:
        return f"https://api.lever.co/v0/postings/{quote(external_identifier, safe='')}?mode=json"
    if slug == JobSource.ASHBY:
        return "https://jobs.ashbyhq.com"
    return None


class InvalidApplicationTransitionError(ValueError):
    pass


class DuplicateApplicationError(ValueError):
    def __init__(self, application: Application) -> None:
        self.application = application
        super().__init__(
            f"Application already exists for user={application.user_id} job={application.job_id}."
        )


class JobFocusRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_primary_user(self) -> User | None:
        return self.session.scalars(
            select(User)
            .options(selectinload(User.profile), selectinload(User.user_preferences))
            .order_by(User.created_at.asc())
        ).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.session.scalars(
            select(User)
            .options(selectinload(User.profile), selectinload(User.user_preferences))
            .where(User.email == email)
        ).first()

    def get_profile_for_user(self, user_id: str) -> Profile | None:
        return self.session.scalars(select(Profile).where(Profile.user_id == user_id)).first()

    def get_preferences_for_user(self, user_id: str) -> UserPreference | None:
        return self.session.scalars(
            select(UserPreference).where(UserPreference.user_id == user_id)
        ).first()

    def get_default_resume_for_user(self, user_id: str) -> Resume | None:
        resume = self.session.scalars(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_default.is_(True))
            .order_by(Resume.version.desc())
        ).first()
        if resume is not None:
            return resume

        return self.session.scalars(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.version.desc())
        ).first()

    def list_jobs(self) -> list[Job]:
        return list(
            self.session.scalars(
                select(Job)
                .options(selectinload(Job.job_source))
                .order_by(Job.posted_at.desc())
            ).all()
        )

    def list_job_sources(self) -> list[JobSourceConfig]:
        return list(
            self.session.scalars(
                select(JobSourceConfig)
                .options(selectinload(JobSourceConfig.jobs))
                .order_by(JobSourceConfig.display_name.asc(), JobSourceConfig.created_at.asc())
            ).all()
        )

    def list_source_registry(self) -> list[JobSourceConfig]:
        return list(
            self.session.scalars(
                select(JobSourceConfig)
                .order_by(JobSourceConfig.display_name.asc(), JobSourceConfig.created_at.asc())
            ).all()
        )

    def list_source_registry_dtos(
        self,
        *,
        last_ingest_at: datetime | None = None,
    ) -> list[SourceRegistryDTO]:
        sources = self.list_source_registry()
        stats_by_source_id = self._load_source_job_stats(source.id for source in sources)
        return [
            self.to_source_registry_dto(
                source,
                last_ingest_at=last_ingest_at,
                stats=stats_by_source_id.get(source.id),
            )
            for source in sources
        ]

    def list_active_ingest_sources(self) -> list[JobSourceConfig]:
        return list(
            self.session.scalars(
                select(JobSourceConfig)
                .where(
                    JobSourceConfig.is_active.is_(True),
                    JobSourceConfig.slug.in_(tuple(AUTOMATED_SOURCE_SLUGS)),
                    JobSourceConfig.external_identifier.is_not(None),
                )
                .order_by(JobSourceConfig.display_name.asc(), JobSourceConfig.created_at.asc())
            ).all()
        )

    def count_configured_live_sources(self) -> int:
        return len(self.list_active_ingest_sources())

    def list_matches_for_user(self, user_id: str) -> list[JobMatch]:
        return list(
            self.session.scalars(
                select(JobMatch)
                .where(JobMatch.user_id == user_id)
                .options(selectinload(JobMatch.job))
                .order_by(JobMatch.match_score.desc())
            ).all()
        )

    def list_applications_for_user(self, user_id: str) -> list[Application]:
        return list(
            self.session.scalars(
                select(Application)
                .where(Application.user_id == user_id)
                .options(
                    selectinload(Application.current_packet),
                    selectinload(Application.events),
                    selectinload(Application.job).selectinload(Job.job_source),
                    selectinload(Application.job).selectinload(Job.job_matches),
                )
                .order_by(Application.updated_at.desc())
            ).all()
        )

    def get_job(self, job_id: str) -> Job | None:
        return self.session.scalars(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.job_source))
        ).first()

    def get_job_source(self, source_id: str) -> JobSourceConfig | None:
        return self.session.scalars(
            select(JobSourceConfig)
            .where(JobSourceConfig.id == source_id)
            .options(selectinload(JobSourceConfig.jobs))
        ).first()

    def get_job_source_by_slug_identifier(
        self,
        slug: JobSource,
        external_identifier: str | None,
    ) -> JobSourceConfig | None:
        statement = select(JobSourceConfig).where(JobSourceConfig.slug == slug)
        if external_identifier is None:
            statement = statement.where(JobSourceConfig.external_identifier.is_(None))
        else:
            statement = statement.where(JobSourceConfig.external_identifier == external_identifier)
        return self.session.scalars(statement).first()

    def get_application_for_job(self, user_id: str, job_id: str) -> Application | None:
        return self.session.scalars(
            select(Application)
            .where(Application.user_id == user_id, Application.job_id == job_id)
            .options(
                selectinload(Application.current_packet),
                selectinload(Application.events),
                selectinload(Application.job).selectinload(Job.job_source),
                selectinload(Application.job).selectinload(Job.job_matches),
            )
        ).first()

    def get_application_for_user(self, user_id: str, application_id: str) -> Application | None:
        return self.session.scalars(
            select(Application)
            .where(Application.user_id == user_id, Application.id == application_id)
            .options(
                selectinload(Application.current_packet),
                selectinload(Application.events),
                selectinload(Application.job).selectinload(Job.job_source),
                selectinload(Application.job).selectinload(Job.job_matches),
            )
        ).first()

    def update_profile(self, profile: Profile, payload: ProfileUpdateDTO) -> Profile:
        profile.full_name = payload.full_name.strip()
        profile.headline = payload.headline.strip()
        profile.location = payload.location.strip()
        profile.target_roles = [role.strip() for role in payload.target_roles if role.strip()]
        profile.years_experience = payload.years_experience
        profile.seniority_level = payload.seniority_level.strip() if payload.seniority_level else None
        profile.authorization_regions = [
            region.strip() for region in payload.authorization_regions if region.strip()
        ]
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_or_create_user_preferences(self, user: User) -> UserPreference:
        existing = self.get_preferences_for_user(user.id)
        if existing is not None:
            return existing

        preferences = UserPreference(user_id=user.id)
        self.session.add(preferences)
        self.session.commit()
        self.session.refresh(preferences)
        return preferences

    def update_user_preferences(
        self, preferences: UserPreference, payload: UserPreferenceUpdateDTO
    ) -> UserPreference:
        preferences.preferred_locations = [
            location.strip() for location in payload.preferred_locations if location.strip()
        ]
        preferences.preferred_work_modes = [mode.value for mode in payload.preferred_work_modes]
        preferences.preferred_employment_types = [
            employment_type.value for employment_type in payload.preferred_employment_types
        ]
        preferences.desired_salary_min = payload.desired_salary_min
        preferences.desired_salary_max = payload.desired_salary_max
        preferences.auto_apply_enabled = payload.auto_apply_enabled
        preferences.auto_apply_min_score = payload.auto_apply_min_score
        self.session.commit()
        self.session.refresh(preferences)
        return preferences

    def get_or_create_job_source(
        self,
        *,
        slug: JobSource,
        external_identifier: str | None = None,
        display_name: str,
        base_url: str | None = None,
        is_active: bool = True,
    ) -> JobSourceConfig:
        source = self.get_job_source_by_slug_identifier(slug, external_identifier)
        resolved_base_url = base_url if base_url is not None else default_source_base_url(
            slug, external_identifier
        )
        if source is not None:
            source.display_name = display_name
            source.base_url = resolved_base_url
            source.is_active = is_active
            self.session.flush()
            return source

        source = JobSourceConfig(
            slug=slug,
            external_identifier=external_identifier,
            display_name=display_name,
            base_url=resolved_base_url,
            is_active=is_active,
        )
        self.session.add(source)
        self.session.flush()
        return source

    def create_job_source(self, payload: SourceCreateDTO) -> JobSourceConfig:
        external_identifier = payload.external_identifier.strip()
        source = self.get_job_source_by_slug_identifier(payload.source, external_identifier)
        if source is not None:
            source.display_name = (
                payload.display_name.strip()
                if payload.display_name and payload.display_name.strip()
                else source.display_name
            )
            source.is_active = payload.is_active
            source.base_url = default_source_base_url(payload.source, external_identifier)
            self.session.commit()
            self.session.refresh(source)
            return source

        source = JobSourceConfig(
            slug=payload.source,
            external_identifier=external_identifier,
            display_name=(
                payload.display_name.strip()
                if payload.display_name and payload.display_name.strip()
                else default_source_display_name(payload.source, external_identifier)
            ),
            base_url=default_source_base_url(payload.source, external_identifier),
            is_active=payload.is_active,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def set_job_source_active(self, source: JobSourceConfig, is_active: bool) -> JobSourceConfig:
        source.is_active = is_active
        self.session.commit()
        self.session.refresh(source)
        return source

    def mark_job_source_sync_requested(
        self,
        source: JobSourceConfig,
        *,
        requested_at: datetime | None = None,
    ) -> JobSourceConfig:
        source.last_sync_requested_at = requested_at or datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(source)
        return source

    def mark_job_source_sync_started(
        self,
        source: JobSourceConfig,
        *,
        started_at: datetime | None = None,
    ) -> JobSourceConfig:
        source.last_sync_started_at = started_at or datetime.now(timezone.utc)
        self.session.flush()
        return source

    def mark_job_source_sync_completed(
        self,
        source: JobSourceConfig,
        *,
        completed_at: datetime | None = None,
        fetched_job_count: int = 0,
        created_job_count: int = 0,
        updated_job_count: int = 0,
        error: str | None = None,
    ) -> JobSourceConfig:
        resolved_completed_at = completed_at or datetime.now(timezone.utc)
        source.last_sync_completed_at = resolved_completed_at
        source.last_fetched_job_count = fetched_job_count
        source.last_created_job_count = created_job_count
        source.last_updated_job_count = updated_job_count
        if error:
            source.last_error = error
            source.last_error_at = resolved_completed_at
        else:
            source.last_successful_sync_at = resolved_completed_at
            source.last_error = None
            source.last_error_at = None
        self.session.flush()
        return source

    def get_job_by_source_external_id(self, source_id: str, external_job_id: str) -> Job | None:
        return self.session.scalars(
            select(Job)
            .where(Job.job_source_id == source_id, Job.external_job_id == external_job_id)
            .options(selectinload(Job.job_source))
        ).first()

    def upsert_discovered_job(
        self,
        *,
        source: JobSourceConfig,
        discovered_job: DiscoveredJobDTO,
    ) -> tuple[Job, bool]:
        normalized_payload = discovered_job.model_dump(mode="json", exclude={"raw_payload"})
        existing = self.get_job_by_source_external_id(source.id, discovered_job.external_job_id)

        if existing is None:
            job = Job(
                job_source_id=source.id,
                external_job_id=discovered_job.external_job_id,
                company=discovered_job.company,
                title=discovered_job.title,
                location=discovered_job.location,
                work_mode=discovered_job.work_mode,
                employment_type=discovered_job.employment_type,
                salary_min=discovered_job.salary_min,
                salary_max=discovered_job.salary_max,
                description=discovered_job.description,
                application_url=discovered_job.application_url,
                seniority_level=discovered_job.seniority_level,
                authorization_requirement=discovered_job.authorization_requirement,
                raw_payload=discovered_job.raw_payload,
                normalized_payload=normalized_payload,
                posted_at=discovered_job.posted_at,
            )
            self.session.add(job)
            self.session.flush()
            return job, True

        existing.company = discovered_job.company
        existing.title = discovered_job.title
        existing.location = discovered_job.location
        existing.work_mode = discovered_job.work_mode
        existing.employment_type = discovered_job.employment_type
        existing.salary_min = discovered_job.salary_min
        existing.salary_max = discovered_job.salary_max
        existing.description = discovered_job.description
        existing.application_url = discovered_job.application_url
        existing.seniority_level = discovered_job.seniority_level
        existing.authorization_requirement = discovered_job.authorization_requirement
        existing.raw_payload = discovered_job.raw_payload
        existing.normalized_payload = normalized_payload
        existing.posted_at = discovered_job.posted_at
        self.session.flush()
        return existing, False

    def create_application_packet(
        self,
        *,
        user: User,
        job: Job,
        resume: Resume | None,
        status: PacketStatus,
        tailored_resume_summary: str | None = None,
        cover_note: str | None = None,
        screening_answers: dict | None = None,
        missing_fields: Iterable[str] | None = None,
    ) -> ApplicationPacket:
        packet = ApplicationPacket(
            user_id=user.id,
            job_id=job.id,
            resume_id=resume.id if resume is not None else None,
            status=status,
            selected_resume_version=resume.version if resume is not None else None,
            tailored_resume_summary=tailored_resume_summary,
            cover_note=cover_note,
            screening_answers=dict(screening_answers or {}),
            missing_fields=list(missing_fields or []),
        )
        self.session.add(packet)
        self.session.flush()
        return packet

    def create_application(
        self,
        *,
        user: User,
        job: Job,
        initial_status: ApplicationStatus = ApplicationStatus.DISCOVERED,
        notes: str = "",
        current_packet: ApplicationPacket | None = None,
        actor: str = "system",
    ) -> Application:
        existing = self.get_application_for_job(user.id, job.id)
        if existing is not None:
            raise DuplicateApplicationError(existing)

        application = Application(
            user_id=user.id,
            job_id=job.id,
            current_packet_id=current_packet.id if current_packet is not None else None,
            status=initial_status,
            notes=notes,
        )
        self.session.add(application)
        self.session.flush()
        self._record_event(
            application=application,
            from_status=None,
            to_status=initial_status,
            event_type="created",
            actor=actor,
            note=notes or None,
            payload={},
        )
        self.session.commit()
        self.session.refresh(application)
        return application

    def transition_application_status(
        self,
        application: Application,
        next_status: ApplicationStatus,
        *,
        actor: str = "system",
        note: str | None = None,
        payload: dict | None = None,
        current_packet: ApplicationPacket | None = None,
        duplicate_of: Application | None = None,
        last_error: str | None = None,
        blocking_reason: str | None = None,
    ) -> Application:
        allowed = ALLOWED_APPLICATION_TRANSITIONS[application.status]
        if next_status not in allowed:
            raise InvalidApplicationTransitionError(
                f"Cannot transition application from {application.status.value} to {next_status.value}."
            )

        previous_status = application.status
        application.status = next_status

        if current_packet is not None:
            application.current_packet_id = current_packet.id

        if next_status == ApplicationStatus.SUBMITTED:
            application.submitted_at = datetime.now(timezone.utc)

        if next_status == ApplicationStatus.FAILED:
            application.last_error = last_error or note

        if next_status == ApplicationStatus.BLOCKED:
            application.blocking_reason = blocking_reason or note

        if next_status == ApplicationStatus.DUPLICATE and duplicate_of is not None:
            application.duplicate_of_application_id = duplicate_of.id

        if note:
            application.notes = f"{application.notes}\n{note}".strip() if application.notes else note

        self._record_event(
            application=application,
            from_status=previous_status,
            to_status=next_status,
            event_type="status_changed",
            actor=actor,
            note=note,
            payload=payload or {},
        )
        self.session.commit()
        self.session.refresh(application)
        return application

    def create_auth_session(self, user: User, token_hash: str, expires_at: datetime) -> AuthSession:
        auth_session = AuthSession(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(auth_session)
        self.session.commit()
        self.session.refresh(auth_session)
        return auth_session

    def has_application_event(self, application_id: str, event_type: str) -> bool:
        return (
            self.session.scalars(
                select(ApplicationEvent.id).where(
                    ApplicationEvent.application_id == application_id,
                    ApplicationEvent.event_type == event_type,
                )
            ).first()
            is not None
        )

    def record_application_event(
        self,
        *,
        application: Application,
        event_type: str,
        actor: str,
        note: str | None = None,
        payload: dict | None = None,
        from_status: ApplicationStatus | None = None,
        to_status: ApplicationStatus | None = None,
        commit: bool = True,
    ) -> ApplicationEvent:
        event = self._record_event(
            application=application,
            from_status=from_status,
            to_status=to_status or application.status,
            event_type=event_type,
            actor=actor,
            note=note,
            payload=payload or {},
        )
        if commit:
            self.session.commit()
        return event

    def to_user_profile_dto(self, user: User) -> UserProfileDTO:
        profile = user.profile
        if profile is None:
            raise ValueError("User is missing profile data.")
        return UserProfileDTO(
            id=user.id,
            email=user.email,
            full_name=profile.full_name,
            headline=profile.headline,
            location=profile.location,
            target_roles=profile.target_roles,
            years_experience=profile.years_experience,
            seniority_level=profile.seniority_level,
            authorization_regions=profile.authorization_regions,
            created_at=user.created_at,
        )

    def to_user_preference_dto(self, preferences: UserPreference) -> UserPreferenceDTO:
        return UserPreferenceDTO(
            id=preferences.id,
            user_id=preferences.user_id,
            preferred_locations=preferences.preferred_locations,
            preferred_work_modes=[
                WorkMode(value) for value in preferences.preferred_work_modes if value
            ],
            preferred_employment_types=[
                EmploymentType(value)
                for value in preferences.preferred_employment_types
                if value
            ],
            desired_salary_min=preferences.desired_salary_min,
            desired_salary_max=preferences.desired_salary_max,
            auto_apply_enabled=preferences.auto_apply_enabled,
            auto_apply_min_score=preferences.auto_apply_min_score,
            updated_at=preferences.updated_at,
        )

    def to_resume_dto(self, resume: Resume) -> ResumeDTO:
        return ResumeDTO(
            id=resume.id,
            user_id=resume.user_id,
            version=resume.version,
            title=resume.title,
            file_name=resume.file_name,
            summary=resume.summary,
            skills=resume.skills,
            is_default=resume.is_default,
            updated_at=resume.updated_at,
        )

    def to_job_dto(self, job: Job) -> JobDTO:
        return JobDTO(
            id=job.id,
            source_id=job.job_source_id,
            external_job_id=job.external_job_id,
            company=job.company,
            title=job.title,
            location=job.location,
            work_mode=job.work_mode,
            employment_type=job.employment_type,
            source=job.job_source.slug,
            source_display_name=job.job_source.display_name,
            source_external_identifier=job.job_source.external_identifier,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            description=job.description,
            application_url=job.application_url,
            seniority_level=job.seniority_level,
            authorization_requirement=job.authorization_requirement,
            posted_at=job.posted_at,
        )

    def to_match_dto(self, job_match: JobMatch) -> MatchDTO:
        return MatchDTO(
            id=job_match.id,
            user_id=job_match.user_id,
            job_id=job_match.job_id,
            score=job_match.match_score,
            strength=job_match.strength,
            rationale=job_match.rationale,
            why_matched=job_match.why_matched,
            created_at=job_match.created_at,
        )

    def to_application_packet_dto(self, packet: ApplicationPacket) -> ApplicationPacketDTO:
        return ApplicationPacketDTO(
            id=packet.id,
            user_id=packet.user_id,
            job_id=packet.job_id,
            resume_id=packet.resume_id,
            status=packet.status,
            selected_resume_version=packet.selected_resume_version,
            tailored_resume_summary=packet.tailored_resume_summary,
            cover_note=packet.cover_note,
            screening_answers={key: str(value) for key, value in packet.screening_answers.items()},
            missing_fields=[str(field) for field in packet.missing_fields],
            updated_at=packet.updated_at,
        )

    def to_application_event_dto(self, event: ApplicationEvent) -> ApplicationEventDTO:
        return ApplicationEventDTO(
            id=event.id,
            application_id=event.application_id,
            from_status=event.from_status,
            to_status=event.to_status,
            event_type=event.event_type,
            actor=event.actor,
            note=event.note,
            payload=event.payload,
            created_at=event.created_at,
        )

    def to_application_dto(self, application: Application) -> ApplicationDTO:
        packet = application.current_packet
        job = application.job
        events = sorted(application.events, key=lambda event: event.created_at)
        latest_error_code = self._extract_latest_error_code(events)
        confirmation_details = self._extract_confirmation_details(events)
        match = next(
            (
                candidate
                for candidate in getattr(job, "job_matches", [])
                if candidate.user_id == application.user_id
            ),
            None,
        )
        return ApplicationDTO(
            id=application.id,
            user_id=application.user_id,
            job_id=application.job_id,
            status=application.status,
            packet_id=application.current_packet_id,
            packet_status=packet.status if packet is not None else None,
            notes=application.notes,
            submitted_at=application.submitted_at,
            last_error=application.last_error,
            blocking_reason=application.blocking_reason,
            latest_error_code=latest_error_code,
            confirmation_details=confirmation_details,
            job=self.to_job_dto(job),
            match_score=match.match_score if match is not None else None,
            match_strength=match.strength if match is not None else None,
            packet=self.to_application_packet_dto(packet) if packet is not None else None,
            events=[self.to_application_event_dto(event) for event in events],
            created_at=application.created_at,
            updated_at=application.updated_at,
        )

    def list_source_health(
        self,
        *,
        last_ingest_at: datetime | None = None,
    ) -> list[SourceHealthDTO]:
        return [
            self.to_source_health_dto(source, last_ingest_at=last_ingest_at)
            for source in self.list_job_sources()
        ]

    def to_source_health_dto(
        self,
        source: JobSourceConfig,
        *,
        last_ingest_at: datetime | None = None,
    ) -> SourceHealthDTO:
        stats = self._build_source_job_stats_from_jobs(source.jobs)
        last_seen_at = stats.last_seen_at or source.last_successful_sync_at or last_ingest_at
        status, note = self._resolve_source_health_from_stats(source, stats, last_ingest_at)
        return SourceHealthDTO(
            id=source.id,
            source=source.slug,
            display_name=source.display_name,
            external_identifier=source.external_identifier,
            base_url=source.base_url,
            status=status,
            is_active=source.is_active,
            job_count=stats.job_count,
            last_seen_at=last_seen_at,
            last_posted_at=stats.last_posted_at,
            last_sync_requested_at=source.last_sync_requested_at,
            last_sync_started_at=source.last_sync_started_at,
            last_sync_completed_at=source.last_sync_completed_at,
            last_successful_sync_at=source.last_successful_sync_at,
            last_error=source.last_error,
            last_error_at=source.last_error_at,
            last_fetched_job_count=source.last_fetched_job_count or 0,
            last_created_job_count=source.last_created_job_count or 0,
            last_updated_job_count=source.last_updated_job_count or 0,
            note=note,
        )

    def to_source_registry_dto(
        self,
        source: JobSourceConfig,
        *,
        last_ingest_at: datetime | None = None,
        stats: SourceJobStats | None = None,
    ) -> SourceRegistryDTO:
        resolved_stats = stats or self._build_source_job_stats_from_jobs(source.jobs)
        status, note = self._resolve_source_health_from_stats(
            source,
            resolved_stats,
            last_ingest_at,
        )
        return SourceRegistryDTO(
            id=source.id,
            source=source.slug,
            display_name=source.display_name,
            external_identifier=source.external_identifier,
            base_url=source.base_url,
            is_active=source.is_active,
            tracked_job_count=resolved_stats.job_count,
            status=status,
            last_sync_requested_at=source.last_sync_requested_at,
            last_sync_started_at=source.last_sync_started_at,
            last_sync_completed_at=source.last_sync_completed_at,
            last_successful_sync_at=source.last_successful_sync_at,
            last_error=source.last_error,
            last_error_at=source.last_error_at,
            last_fetched_job_count=source.last_fetched_job_count or 0,
            last_created_job_count=source.last_created_job_count or 0,
            last_updated_job_count=source.last_updated_job_count or 0,
            note=note,
        )

    def to_auth_session_dto(self, token: str, user: User) -> AuthSessionDTO:
        return AuthSessionDTO(access_token=token, token_type="bearer", user=self.to_user_profile_dto(user))

    def validate_login_request(self, email: str, password: str) -> LoginRequestDTO:
        return LoginRequestDTO(email=email, password=password)

    def _record_event(
        self,
        *,
        application: Application,
        from_status: ApplicationStatus | None,
        to_status: ApplicationStatus,
        event_type: str,
        actor: str,
        note: str | None,
        payload: dict,
    ) -> ApplicationEvent:
        event = ApplicationEvent(
            application_id=application.id,
            from_status=from_status,
            to_status=to_status,
            event_type=event_type,
            actor=actor,
            note=note,
            payload=payload,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def _extract_latest_error_code(self, events: list[ApplicationEvent]) -> str | None:
        for event in reversed(events):
            payload = event.payload if isinstance(event.payload, dict) else {}
            error_code = payload.get("errorCode")
            if isinstance(error_code, str) and error_code:
                return error_code
        return None

    def _extract_confirmation_details(
        self, events: list[ApplicationEvent]
    ) -> dict[str, Any] | None:
        for event in reversed(events):
            if event.event_type not in {"apply_succeeded", "submission_confirmed"}:
                continue
            if isinstance(event.payload, dict) and event.payload:
                return event.payload
        return None

    def _resolve_source_health(
        self,
        source: JobSourceConfig,
        jobs: list[Job],
        last_ingest_at: datetime | None,
    ) -> tuple[SourceHealthStatus, str]:
        return self._resolve_source_health_from_stats(
            source,
            self._build_source_job_stats_from_jobs(jobs),
            last_ingest_at,
        )

    def _resolve_source_health_from_stats(
        self,
        source: JobSourceConfig,
        stats: SourceJobStats,
        last_ingest_at: datetime | None,
    ) -> tuple[SourceHealthStatus, str]:
        if not source.is_active:
            return (
                SourceHealthStatus.INACTIVE,
                (
                    "Manual intake only. Automated discovery is intentionally disabled."
                    if source.slug in MANUAL_ONLY_SOURCE_SLUGS
                    else "Source is disabled and will be skipped by scheduled ingest runs."
                ),
            )
        if source.slug not in AUTOMATED_SOURCE_SLUGS:
            return (
                SourceHealthStatus.WARNING,
                "This provider is stored, but no automated ingest adapter is enabled for it.",
            )
        if not source.external_identifier:
            return (
                SourceHealthStatus.WARNING,
                "Source is missing its external identifier, so the worker cannot sync it yet.",
            )
        if source.last_error and (
            source.last_successful_sync_at is None
            or (
                source.last_error_at is not None
                and source.last_error_at >= source.last_successful_sync_at
            )
        ):
            return (
                SourceHealthStatus.WARNING,
                f"Latest sync failed: {source.last_error}",
            )
        if source.last_sync_started_at is None:
            return (
                SourceHealthStatus.WARNING,
                "Source is configured, but the worker has not synced it yet.",
            )
        if stats.job_count == 0:
            return (
                SourceHealthStatus.WARNING,
                "Source is active, but no jobs were discovered during the latest sync.",
            )

        freshest_job = stats.last_seen_at
        if freshest_job is None:
            return (
                SourceHealthStatus.WARNING,
                "Source is active, but no jobs were discovered during the latest sync.",
            )
        reference_time = (
            source.last_successful_sync_at
            or source.last_sync_completed_at
            or last_ingest_at
            or freshest_job
        )
        if (reference_time - freshest_job).days >= 3:
            return (
                SourceHealthStatus.WARNING,
                "Source is active, but the job catalog looks stale compared with recent worker runs.",
            )

        return (
            SourceHealthStatus.HEALTHY,
            "Latest sync succeeded and the source is producing jobs.",
        )

    def _load_source_job_stats(self, source_ids: Iterable[str]) -> dict[str, SourceJobStats]:
        source_id_list = list(source_ids)
        if not source_id_list:
            return {}

        rows = self.session.execute(
            select(
                Job.job_source_id,
                func.count(Job.id),
                func.max(Job.updated_at),
                func.max(Job.posted_at),
            )
            .where(Job.job_source_id.in_(source_id_list))
            .group_by(Job.job_source_id)
        ).all()
        return {
            str(source_id): SourceJobStats(
                job_count=int(job_count or 0),
                last_seen_at=last_seen_at,
                last_posted_at=last_posted_at,
            )
            for source_id, job_count, last_seen_at, last_posted_at in rows
        }

    def _build_source_job_stats_from_jobs(self, jobs: Iterable[Job]) -> SourceJobStats:
        job_list = list(jobs)
        updated_values = [job.updated_at for job in job_list if job.updated_at is not None]
        posted_values = [job.posted_at for job in job_list if job.posted_at is not None]
        return SourceJobStats(
            job_count=len(job_list),
            last_seen_at=max(updated_values, default=None),
            last_posted_at=max(posted_values, default=None),
        )
