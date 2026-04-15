from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timezone

from app.models import Application, ApplicationPacket, Job, JobMatch, User
from app.repositories import DuplicateApplicationError, JobFocusRepository
from app.db import normalize_database_url
from job_focus_shared import (
    ApplicationStatus,
    JobSource,
    PacketStatus,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from worker.adapters import build_source_adapters
from worker.adapters.base import SourceAdapter
from worker.clients.tracker import TrackerStore
from worker.clients.http import HttpRequestError
from worker.config import WorkerSettings
from worker.execution import (
    ApplicationExecutor,
    ERROR_BROWSER_FALLBACK_DISABLED,
    ERROR_DUPLICATE_SUBMISSION,
    ERROR_UNSUPPORTED_SOURCE,
    SubmissionSuccess,
    build_application_executor,
    should_return_to_waiting_review,
)
from worker.matching import calculate_match, populate_job_match
from worker.packets import generate_packet_draft

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    normalized_database_url = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if normalized_database_url.startswith("sqlite") else {}
    engine = create_engine(normalized_database_url, future=True, connect_args=connect_args)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ingest_jobs(
    session: Session,
    tracker: TrackerStore,
    settings: WorkerSettings | None = None,
    adapters: Sequence[SourceAdapter] | None = None,
    run_at: datetime | None = None,
) -> dict[str, int]:
    run_at = run_at or utc_now()
    settings = settings or WorkerSettings()
    repository = JobFocusRepository(session)
    adapter_list = (
        list(adapters)
        if adapters is not None
        else build_source_adapters(settings, repository.list_active_ingest_sources())
    )
    fetched_jobs = 0
    created_jobs = 0
    updated_jobs = 0

    for adapter in adapter_list:
        source = (
            repository.get_job_source(adapter.source_id)
            if adapter.source_id is not None
            else None
        )
        if source is None:
            source = repository.get_or_create_job_source(
                slug=adapter.slug,
                external_identifier=adapter.source_external_identifier,
                display_name=adapter.source_display_name,
                base_url=adapter.base_url,
            )
        repository.mark_job_source_sync_started(source, started_at=run_at)
        try:
            discovered_jobs = adapter.fetch_jobs(run_at=run_at)
        except HttpRequestError as error:
            logger.warning("ingest: adapter %s failed: %s", adapter.name, error)
            repository.mark_job_source_sync_completed(
                source,
                completed_at=run_at,
                fetched_job_count=0,
                created_job_count=0,
                updated_job_count=0,
                error=str(error),
            )
            continue

        source_fetched_jobs = len(discovered_jobs)
        source_created_jobs = 0
        source_updated_jobs = 0
        fetched_jobs += source_fetched_jobs
        for discovered_job in discovered_jobs:
            if discovered_job.source != adapter.slug:
                logger.warning(
                    "ingest: adapter %s returned source %s, expected %s",
                    adapter.name,
                    discovered_job.source.value,
                    adapter.slug.value,
                )
                continue
            _, created = repository.upsert_discovered_job(
                source=source,
                discovered_job=discovered_job,
            )
            if created:
                source_created_jobs += 1
                created_jobs += 1
            else:
                source_updated_jobs += 1
                updated_jobs += 1
        repository.mark_job_source_sync_completed(
            source,
            completed_at=run_at,
            fetched_job_count=source_fetched_jobs,
            created_job_count=source_created_jobs,
            updated_job_count=source_updated_jobs,
        )

    session.commit()
    tracker.record("ingest", run_at)
    return {
        "source_count": len(adapter_list),
        "fetched_jobs": fetched_jobs,
        "created_jobs": created_jobs,
        "updated_jobs": updated_jobs,
    }


def score_jobs(session: Session, tracker: TrackerStore, run_at: datetime | None = None) -> dict[str, int]:
    run_at = run_at or utc_now()
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        tracker.record("score", run_at)
        return {"created_matches": 0, "updated_matches": 0}

    resume = repository.get_default_resume_for_user(user.id)
    created_matches = 0
    updated_matches = 0

    for job in repository.list_jobs():
        existing_match = session.scalars(
            select(JobMatch).where(JobMatch.user_id == user.id, JobMatch.job_id == job.id)
        ).first()
        result = calculate_match(user, resume, job)
        if existing_match is None:
            match = JobMatch(user_id=user.id, job_id=job.id)
            populate_job_match(match, result)
            match.created_at = run_at
            match.updated_at = run_at
            session.add(match)
            created_matches += 1
            continue

        populate_job_match(existing_match, result)
        existing_match.updated_at = run_at
        updated_matches += 1

    session.commit()
    tracker.record("score", run_at)
    return {"created_matches": created_matches, "updated_matches": updated_matches}


def generate_packets(
    session: Session,
    tracker: TrackerStore,
    settings: WorkerSettings,
    run_at: datetime | None = None,
) -> dict[str, int]:
    run_at = run_at or utc_now()
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        tracker.record("packet", run_at)
        return {"ready_packets": 0}

    resume = repository.get_default_resume_for_user(user.id)
    ready_packets = 0
    matches = repository.list_matches_for_user(user.id)

    for match in matches:
        if match.match_score < settings.auto_apply_min_score:
            continue

        job = repository.get_job(match.job_id)
        if job is None:
            continue

        application = repository.get_application_for_job(user.id, job.id)
        if application is None:
            try:
                application = repository.create_application(
                    user=user,
                    job=job,
                    initial_status=ApplicationStatus.DISCOVERED,
                    notes="Auto-created from a high-scoring worker match.",
                    actor="worker",
                )
            except DuplicateApplicationError as error:
                application = error.application

        if application.status == ApplicationStatus.DISCOVERED:
            application = repository.transition_application_status(
                application,
                ApplicationStatus.SHORTLISTED,
                actor="worker",
                note="Worker shortlisted this match for packet generation.",
                payload={"matchScore": match.match_score},
            )

        if application.current_packet is None and application.status == ApplicationStatus.SHORTLISTED:
            packet_draft = generate_packet_draft(
                user=user,
                resume=resume,
                job=job,
                why_matched=match.why_matched,
            )
            packet = repository.create_application_packet(
                user=user,
                job=job,
                resume=resume,
                status=packet_draft.status,
                tailored_resume_summary=packet_draft.tailored_resume_summary,
                cover_note=packet_draft.cover_note,
                screening_answers=packet_draft.screening_answers,
                missing_fields=packet_draft.missing_fields,
            )
            if packet_draft.status == PacketStatus.NEEDS_USER_INPUT:
                repository.transition_application_status(
                    application,
                    ApplicationStatus.NEEDS_USER_INPUT,
                    actor="worker",
                    note="Packet generation needs more approved profile data before review.",
                    current_packet=packet,
                    payload={"packetId": packet.id, "missingFields": packet_draft.missing_fields},
                )
                continue

            application = repository.transition_application_status(
                application,
                ApplicationStatus.DRAFT_READY,
                actor="worker",
                note="Worker generated the initial application packet draft.",
                current_packet=packet,
                payload={"packetId": packet.id},
            )
            application = repository.transition_application_status(
                application,
                ApplicationStatus.WAITING_REVIEW,
                actor="worker",
                note="Packet is ready for review before submission.",
                current_packet=packet,
                payload={"packetId": packet.id},
            )
            ready_packets += 1

    tracker.record("packet", run_at)
    return {"ready_packets": ready_packets}


def apply_jobs(
    session: Session,
    tracker: TrackerStore,
    settings: WorkerSettings | None = None,
    executor: ApplicationExecutor | None = None,
    run_at: datetime | None = None,
) -> dict[str, int]:
    run_at = run_at or utc_now()
    settings = settings or WorkerSettings()
    repository = JobFocusRepository(session)
    application_executor = executor or build_application_executor(
        browser_fallback_enabled=settings.browser_fallback_enabled,
        browser_assist_enabled=settings.browser_assist_enabled,
        browser_headless=settings.browser_headless,
        browser_auth_state_dir=settings.resolved_browser_auth_state_dir,
        resume_storage_dir=settings.resolved_browser_resume_storage_dir,
        timeout_seconds=settings.ats_apply_timeout_seconds,
    )
    submitted = 0
    failed = 0
    blocked = 0
    skipped = 0

    applications = session.scalars(
        select(Application)
        .where(Application.status == ApplicationStatus.SUBMITTING)
        .options(
            selectinload(Application.current_packet).selectinload(ApplicationPacket.resume),
            selectinload(Application.job).selectinload(Job.job_source),
            selectinload(Application.user).selectinload(User.profile),
            selectinload(Application.user).selectinload(User.user_preferences),
        )
    ).all()

    for application in applications:
        if repository.has_application_event(application.id, "submission_succeeded"):
            repository.record_application_event(
                application=application,
                event_type="submission_skipped",
                actor="worker",
                note="Skipped submission because a prior success event already exists.",
                payload={"reason": "already_submitted"},
            )
            skipped += 1
            continue

        if application.current_packet is None or application.job is None or application.user is None:
            repository.transition_application_status(
                application,
                ApplicationStatus.BLOCKED,
                actor="worker",
                note="Cannot submit without a loaded job, user, and packet.",
                payload={"errorCode": "missing_submission_context"},
                blocking_reason="missing_submission_context",
            )
            blocked += 1
            continue

        if (
            application.job.job_source.slug not in {JobSource.GREENHOUSE, JobSource.LEVER}
            and not settings.browser_automation_enabled
        ):
            repository.record_application_event(
                application=application,
                event_type="submission_attempted",
                actor="worker",
                note="Submission attempt blocked because the ATS source is unsupported.",
                payload={
                    "source": application.job.job_source.slug.value,
                    "errorCode": ERROR_UNSUPPORTED_SOURCE,
                },
            )
            repository.transition_application_status(
                application,
                ApplicationStatus.BLOCKED,
                actor="worker",
                note="No supported ATS execution adapter is available for this job source.",
                payload={
                    "source": application.job.job_source.slug.value,
                    "errorCode": ERROR_UNSUPPORTED_SOURCE,
                },
                blocking_reason=ERROR_UNSUPPORTED_SOURCE,
            )
            blocked += 1
            continue

        repository.record_application_event(
            application=application,
            event_type="submission_attempted",
            actor="worker",
            note="Worker started an ATS submission attempt.",
            payload={
                "source": application.job.job_source.slug.value,
                "applicationUrl": application.job.application_url,
                "idempotencyKey": application.id,
            },
        )

        result = application_executor.submit(
            application=application,
            user=application.user,
            job=application.job,
            packet=application.current_packet,
        )

        if isinstance(result, SubmissionSuccess):
            application.current_packet.status = PacketStatus.FINALIZED
            success_payload = {
                **result.payload,
                "confirmationId": result.confirmation_id,
                "confirmationMessage": result.confirmation_message,
                "confirmationUrl": result.confirmation_url,
                "submittedAt": result.submitted_at.isoformat(),
            }
            repository.record_application_event(
                application=application,
                event_type="submission_succeeded",
                actor="worker",
                note="ATS submission succeeded.",
                payload=success_payload,
            )
            repository.transition_application_status(
                application,
                ApplicationStatus.SUBMITTED,
                actor="worker",
                note=(
                    f"Worker submitted the application successfully."
                    f"{f' Confirmation ID: {result.confirmation_id}.' if result.confirmation_id else ''}"
                ),
                payload=success_payload,
            )
            submitted += 1
            continue

        failure_payload = result.payload
        repository.record_application_event(
            application=application,
            event_type="submission_failed",
            actor="worker",
            note=result.message,
            payload=failure_payload,
        )
        if result.error_code == ERROR_DUPLICATE_SUBMISSION:
            repository.transition_application_status(
                application,
                ApplicationStatus.DUPLICATE,
                actor="worker",
                note="ATS indicated this job was already submitted.",
                payload=failure_payload,
            )
            blocked += 1
            continue

        if should_return_to_waiting_review(result.error_code):
            repository.record_application_event(
                application=application,
                event_type="submission_review_required",
                actor="worker",
                note=result.message,
                payload=failure_payload,
            )
            repository.transition_application_status(
                application,
                ApplicationStatus.WAITING_REVIEW,
                actor="worker",
                note=result.message,
                payload=failure_payload,
                current_packet=application.current_packet,
            )
            skipped += 1
            continue

        if result.error_code in {ERROR_UNSUPPORTED_SOURCE, ERROR_BROWSER_FALLBACK_DISABLED}:
            repository.transition_application_status(
                application,
                ApplicationStatus.BLOCKED,
                actor="worker",
                note=result.message,
                payload=failure_payload,
                blocking_reason=result.error_code,
            )
            blocked += 1
            continue

        repository.transition_application_status(
            application,
            ApplicationStatus.FAILED,
            actor="worker",
            note=result.message,
            payload=failure_payload,
            last_error=result.error_code,
        )
        failed += 1

    tracker.record("apply", run_at)
    return {
        "submitted_applications": submitted,
        "failed_applications": failed,
        "blocked_applications": blocked,
        "skipped_applications": skipped,
    }
