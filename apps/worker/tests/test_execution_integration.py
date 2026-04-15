from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import reset_settings_cache
from app.db.session import create_all_tables, reset_engine, session_scope
from app.models import Application, ApplicationEvent, ApplicationPacket
from app.repositories import JobFocusRepository
from app.services.seeding import seed_demo_data
from job_focus_shared import (
    ApplicationStatus,
    DiscoveredJobDTO,
    EmploymentType,
    JobSource,
    PacketStatus,
    WorkMode,
)
from sqlalchemy import select

from worker.config import WorkerSettings
from worker.execution import (
    ERROR_BROWSER_REVIEW_REQUIRED,
    SubmissionFailure,
    SubmissionTransportResponse,
    build_application_executor,
)
from worker.tasks.pipeline import apply_jobs


class DummyTracker:
    def __init__(self) -> None:
        self.events: dict[str, str] = {}

    def record(self, task_name: str, run_at) -> None:  # noqa: ANN001
        self.events[task_name] = run_at.isoformat()


class MockSubmissionTransport:
    def __init__(self, responses_by_url: dict[str, SubmissionTransportResponse]) -> None:
        self.responses_by_url = responses_by_url
        self.calls: list[dict] = []

    def post_json(self, url: str, payload: dict, *, headers: dict | None = None) -> SubmissionTransportResponse:
        self.calls.append({"url": url, "payload": payload, "headers": headers or {}})
        return self.responses_by_url[url]


class MockBrowserAssistService:
    def __init__(self, result) -> None:  # noqa: ANN001
        self.result = result
        self.calls: list[dict[str, str]] = []

    def submit(self, *, application, user, job, packet):  # noqa: ANN001
        self.calls.append({"application_id": application.id, "job_id": job.id})
        return self.result


def test_apply_jobs_submits_supported_ats_sources_and_persists_confirmation_details(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "job_focus_apply_success.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        seed_demo_data(session)
        repository = JobFocusRepository(session)
        user = repository.get_primary_user()
        assert user is not None
        resume = repository.get_default_resume_for_user(user.id)
        assert resume is not None
        greenhouse_job, lever_job = repository.list_jobs()[:2]
        greenhouse_application = repository.get_application_for_job(user.id, greenhouse_job.id)
        assert greenhouse_application is not None
        greenhouse_application.status = ApplicationStatus.SUBMITTING
        existing_application = repository.get_application_for_job(user.id, lever_job.id)
        assert existing_application is not None
        packet = repository.create_application_packet(
            user=user,
            job=lever_job,
            resume=resume,
            status=PacketStatus.WAITING_REVIEW,
            tailored_resume_summary="Tailored for systems-heavy operations leadership.",
            cover_note="Grounded in structured profile data only.",
            screening_answers={
                "work_authorization": "Authorized to work in the United States.",
                "years_experience": "8 years of relevant experience.",
            },
            missing_fields=[],
        )
        existing_application.status = ApplicationStatus.SUBMITTING
        existing_application.current_packet_id = packet.id
        existing_application.last_error = None
        existing_application.notes = "Ready for ATS submission."
        session.commit()

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        redis_url="redis://localhost:6391/15",
    )
    transport = MockSubmissionTransport(
        {
            "https://boards.greenhouse.io/northstar/jobs/12345": SubmissionTransportResponse(
                status_code=201,
                payload={"confirmation_id": "gh-123", "message": "Application received"},
            ),
            "https://jobs.lever.co/relay/abc123": SubmissionTransportResponse(
                status_code=200,
                payload={"applicationId": "lv-456", "message": "Application submitted"},
            ),
        }
    )
    executor = build_application_executor(transport=transport)

    with session_scope() as session:
        result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        applications = session.scalars(
            select(Application).where(Application.job_id.in_(["c2b7d44e-c26c-418e-a8fe-a23810e51e26", "c46f8d95-d508-4efa-b0f2-8ae0c640d95d"]))
        ).all()
        events = session.scalars(select(ApplicationEvent)).all()
        packets = session.scalars(select(ApplicationPacket)).all()

    assert result["submitted_applications"] == 2
    assert len(transport.calls) == 2
    assert all(application.status == ApplicationStatus.SUBMITTED for application in applications)
    assert all(packet.status == PacketStatus.FINALIZED for packet in packets)
    assert any(
        event.event_type == "submission_succeeded" and event.payload.get("confirmationId") == "gh-123"
        for event in events
    )
    assert any(
        event.event_type == "submission_succeeded" and event.payload.get("confirmationId") == "lv-456"
        for event in events
    )
    assert transport.calls[0]["headers"]["X-JobFocus-Idempotency-Key"]
    assert transport.calls[0]["payload"]["applicationPacket"]["resumeVersion"] == 1

    reset_engine()
    reset_settings_cache()


def test_apply_jobs_persists_normalized_failure_codes_and_attempt_events(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "job_focus_apply_failure.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        seed_demo_data(session)
        application = session.scalars(
            select(Application).where(Application.job_id == "c2b7d44e-c26c-418e-a8fe-a23810e51e26")
        ).first()
        assert application is not None
        application.status = ApplicationStatus.SUBMITTING
        session.commit()

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        redis_url="redis://localhost:6391/15",
    )
    transport = MockSubmissionTransport(
        {
            "https://boards.greenhouse.io/northstar/jobs/12345": SubmissionTransportResponse(
                status_code=422,
                payload={"message": "Screening answers invalid"},
            )
        }
    )
    executor = build_application_executor(transport=transport)

    with session_scope() as session:
        result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        application = session.scalars(
            select(Application).where(Application.job_id == "c2b7d44e-c26c-418e-a8fe-a23810e51e26")
        ).first()
        events = session.scalars(
            select(ApplicationEvent).where(ApplicationEvent.application_id == application.id)
        ).all()
        packet = session.get(ApplicationPacket, application.current_packet_id)

    assert application is not None
    assert result["failed_applications"] == 1
    assert application.status == ApplicationStatus.FAILED
    assert application.last_error == "invalid_packet"
    assert packet is not None
    assert packet.status == PacketStatus.WAITING_REVIEW
    assert any(event.event_type == "submission_attempted" for event in events)
    assert any(
        event.event_type == "submission_failed" and event.payload.get("errorCode") == "invalid_packet"
        for event in events
    )

    reset_engine()
    reset_settings_cache()


def test_apply_jobs_skips_when_a_success_event_already_exists_for_idempotency(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "job_focus_apply_idempotent.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        seed_demo_data(session)
        application = session.scalars(
            select(Application).where(Application.job_id == "c2b7d44e-c26c-418e-a8fe-a23810e51e26")
        ).first()
        assert application is not None
        application.status = ApplicationStatus.SUBMITTING
        session.commit()

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        redis_url="redis://localhost:6391/15",
    )
    transport = MockSubmissionTransport(
        {
            "https://boards.greenhouse.io/northstar/jobs/12345": SubmissionTransportResponse(
                status_code=201,
                payload={"confirmation_id": "gh-123", "message": "Application received"},
            )
        }
    )
    executor = build_application_executor(transport=transport)

    with session_scope() as session:
        first_result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        application = session.scalars(
            select(Application).where(Application.job_id == "c2b7d44e-c26c-418e-a8fe-a23810e51e26")
        ).first()
        assert application is not None
        application.status = ApplicationStatus.SUBMITTING
        application.updated_at = datetime.now(timezone.utc)
        session.commit()

    with session_scope() as session:
        second_result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        application = session.scalars(
            select(Application).where(Application.job_id == "c2b7d44e-c26c-418e-a8fe-a23810e51e26")
        ).first()
        events = session.scalars(
            select(ApplicationEvent).where(ApplicationEvent.application_id == application.id)
        ).all()

    assert first_result["submitted_applications"] == 1
    assert second_result["submitted_applications"] == 0
    assert second_result["skipped_applications"] == 1
    assert len(transport.calls) == 1
    assert any(event.event_type == "submission_skipped" for event in events)

    reset_engine()
    reset_settings_cache()


def test_apply_jobs_returns_to_waiting_review_when_browser_assist_is_uncertain(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "job_focus_apply_browser_review.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        seed_demo_data(session)
        repository = JobFocusRepository(session)
        user = repository.get_primary_user()
        assert user is not None
        resume = repository.get_default_resume_for_user(user.id)
        assert resume is not None
        source = repository.get_or_create_job_source(
            slug=JobSource.MANUAL,
            display_name="Manual Link",
        )
        manual_job, _ = repository.upsert_discovered_job(
            source=source,
            discovered_job=DiscoveredJobDTO(
                source=JobSource.MANUAL,
                external_job_id="browser-review-1",
                company="Example Corp",
                title="Operations Manager",
                location="Remote - US",
                work_mode=WorkMode.REMOTE,
                employment_type=EmploymentType.FULL_TIME,
                salary_min=125000,
                salary_max=145000,
                description="Generic browser-assisted application test.",
                application_url="https://careers.example.com/apply/operations-manager",
                seniority_level="senior",
                authorization_requirement="US work authorization required",
                posted_at=datetime(2026, 4, 14, 8, 0, 0, tzinfo=timezone.utc),
                raw_payload={"fixture": True},
            ),
        )
        packet = repository.create_application_packet(
            user=user,
            job=manual_job,
            resume=resume,
            status=PacketStatus.WAITING_REVIEW,
            tailored_resume_summary="Tailored for generic browser-assisted submission.",
            cover_note="Structured and approved cover note.",
            screening_answers={
                "work_authorization": "Authorized to work in the United States.",
            },
            missing_fields=[],
        )
        repository.create_application(
            user=user,
            job=manual_job,
            initial_status=ApplicationStatus.SUBMITTING,
            current_packet=packet,
            notes="Ready for browser assist.",
            actor="test",
        )
        manual_job_id = manual_job.id

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        redis_url="redis://localhost:6391/15",
        browser_assist_enabled=True,
    )
    browser_service = MockBrowserAssistService(
        SubmissionFailure(
            outcome="failure",
            error_code=ERROR_BROWSER_REVIEW_REQUIRED,
            message="Browser assist could not confidently confirm the page state.",
            retryable=False,
            payload={"issues": ["confirmation_not_detected"]},
        )
    )
    executor = build_application_executor(
        browser_assist_enabled=True,
        browser_fallback_service=browser_service,
    )

    with session_scope() as session:
        result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        application = session.scalars(
            select(Application).where(Application.job_id == manual_job_id)
        ).first()
        assert application is not None
        events = session.scalars(
            select(ApplicationEvent).where(ApplicationEvent.application_id == application.id)
        ).all()

    assert result["skipped_applications"] == 1
    assert result["submitted_applications"] == 0
    assert application.status == ApplicationStatus.WAITING_REVIEW
    assert browser_service.calls
    assert any(event.event_type == "submission_review_required" for event in events)

    reset_engine()
    reset_settings_cache()
