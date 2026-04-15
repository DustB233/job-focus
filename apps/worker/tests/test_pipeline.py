from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import reset_settings_cache
from app.db.session import create_all_tables, reset_engine, session_scope
from app.models import Application, ApplicationPacket, Job, JobMatch
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
from worker.execution import SubmissionTransportResponse, build_application_executor
from worker.tasks.pipeline import apply_jobs, generate_packets, ingest_jobs, score_jobs


class DummyTracker:
    def __init__(self) -> None:
        self.events: dict[str, str] = {}

    def record(self, task_name: str, run_at) -> None:  # noqa: ANN001
        self.events[task_name] = run_at.isoformat()


class StaticAdapter:
    def __init__(
        self,
        jobs: list[DiscoveredJobDTO],
        *,
        name: str = "Greenhouse",
        slug: JobSource = JobSource.GREENHOUSE,
        source_display_name: str = "Greenhouse",
        source_external_identifier: str = "fixture-greenhouse",
        source_id: str | None = None,
        base_url: str = "https://boards-api.greenhouse.io/v1/boards",
    ) -> None:
        self.name = name
        self.slug = slug
        self.source_display_name = source_display_name
        self.source_external_identifier = source_external_identifier
        self.source_id = source_id
        self.base_url = base_url
        self.jobs = jobs

    def fetch_jobs(self, *, run_at=None) -> list[DiscoveredJobDTO]:  # noqa: ANN001
        return list(self.jobs)


class MockSubmissionTransport:
    def __init__(self, responses_by_url: dict[str, SubmissionTransportResponse]) -> None:
        self.responses_by_url = responses_by_url

    def post_json(self, url: str, payload: dict, *, headers: dict | None = None) -> SubmissionTransportResponse:
        return self.responses_by_url[url]


def test_worker_pipeline_enriches_seeded_data(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "job_focus_worker_test.db"
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
        auto_apply_min_score=70,
    )
    executor = build_application_executor(
        transport=MockSubmissionTransport(
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
    )
    adapters = [
        StaticAdapter(
            [
                DiscoveredJobDTO(
                    source=JobSource.GREENHOUSE,
                    external_job_id="northstar-ai-program-manager",
                    company="Northstar Labs",
                    title="AI Program Manager",
                    location="Remote - US",
                    work_mode=WorkMode.REMOTE,
                    employment_type=EmploymentType.FULL_TIME,
                    salary_min=155000,
                    salary_max=185000,
                    description="Lead cross-functional delivery for AI product launches and process automation.",
                    application_url="https://boards.greenhouse.io/northstar/jobs/12345",
                    seniority_level="senior",
                    authorization_requirement="US work authorization required",
                    posted_at=datetime(2026, 4, 11, 18, 0, tzinfo=timezone.utc),
                    raw_payload={"boardToken": "northstar", "fixture": True},
                )
            ],
            source_display_name="Greenhouse / Northstar",
            source_external_identifier="northstar",
            source_id="4de97149-68d8-4a0d-a949-ed9734ec4a8a",
            base_url="https://boards-api.greenhouse.io/v1/boards/northstar",
        ),
        StaticAdapter(
            [
                DiscoveredJobDTO(
                    source=JobSource.LEVER,
                    external_job_id="relay-ops-systems-lead",
                    company="Relay Commerce",
                    title="Operations Systems Lead",
                    location="San Francisco, CA",
                    work_mode=WorkMode.HYBRID,
                    employment_type=EmploymentType.FULL_TIME,
                    salary_min=145000,
                    salary_max=172000,
                    description="Own business systems, recruiting workflows, and operational analytics.",
                    application_url="https://jobs.lever.co/relay/abc123",
                    seniority_level="lead",
                    authorization_requirement="US work authorization required",
                    posted_at=datetime(2026, 4, 10, 14, 0, tzinfo=timezone.utc),
                    raw_payload={"siteName": "relay", "fixture": True},
                )
            ],
            name="Lever",
            slug=JobSource.LEVER,
            source_display_name="Lever / Relay",
            source_external_identifier="relay",
            source_id="4f55cfd6-115e-4e2f-b20d-027c3f0f30af",
            base_url="https://api.lever.co/v0/postings/relay?mode=json",
        ),
    ]

    with session_scope() as session:
        ingest_result = ingest_jobs(session, tracker, settings=settings, adapters=adapters)
        score_result = score_jobs(session, tracker)
        packet_result = generate_packets(session, tracker, settings)
        apply_result = apply_jobs(session, tracker, settings=settings, executor=executor)

    with session_scope() as session:
        jobs = session.scalars(select(Job)).all()
        matches = session.scalars(select(JobMatch)).all()
        applications = session.scalars(select(Application)).all()
        packets = session.scalars(select(ApplicationPacket)).all()

    assert ingest_result["source_count"] == 2
    assert ingest_result["created_jobs"] == 0
    assert score_result["created_matches"] >= 1
    assert packet_result["ready_packets"] == 0
    assert apply_result["submitted_applications"] >= 1
    assert len(jobs) == 3
    assert len(matches) >= 3
    assert any(application.status == ApplicationStatus.SUBMITTED for application in applications)
    assert any(packet.status == PacketStatus.FINALIZED for packet in packets)
    assert len(packets) >= 3
    assert {"ingest", "score", "packet", "apply"} <= tracker.events.keys()

    reset_engine()
    reset_settings_cache()


def test_ingest_jobs_deduplicates_by_source_and_external_job_id(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "job_focus_ingest_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        redis_url="redis://localhost:6391/15",
    )

    first_adapter = StaticAdapter(
        [
            DiscoveredJobDTO(
                source=JobSource.GREENHOUSE,
                external_job_id="acme:12345",
                company="Acme AI",
                title="AI Program Manager",
                location="Remote - US",
                work_mode=WorkMode.REMOTE,
                employment_type=EmploymentType.FULL_TIME,
                salary_min=150000,
                salary_max=180000,
                description="Initial discovery payload.",
                application_url="https://boards.greenhouse.io/acme/jobs/12345",
                seniority_level="senior",
                authorization_requirement="Valid work authorization required.",
                posted_at=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc),
                raw_payload={"revision": 1},
            )
        ]
    )
    second_adapter = StaticAdapter(
        [
            DiscoveredJobDTO(
                source=JobSource.GREENHOUSE,
                external_job_id="acme:12345",
                company="Acme AI",
                title="Senior AI Program Manager",
                location="Remote - US",
                work_mode=WorkMode.REMOTE,
                employment_type=EmploymentType.FULL_TIME,
                salary_min=155000,
                salary_max=190000,
                description="Updated discovery payload.",
                application_url="https://boards.greenhouse.io/acme/jobs/12345",
                seniority_level="lead",
                authorization_requirement="Valid work authorization required.",
                posted_at=datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc),
                raw_payload={"revision": 2},
            )
        ]
    )

    with session_scope() as session:
        first_result = ingest_jobs(
            session,
            tracker,
            settings=settings,
            adapters=[first_adapter],
        )

    with session_scope() as session:
        second_result = ingest_jobs(
            session,
            tracker,
            settings=settings,
            adapters=[second_adapter],
        )

    with session_scope() as session:
        jobs = session.scalars(select(Job)).all()

    assert first_result["created_jobs"] == 1
    assert first_result["updated_jobs"] == 0
    assert second_result["created_jobs"] == 0
    assert second_result["updated_jobs"] == 1
    assert len(jobs) == 1
    assert jobs[0].title == "Senior AI Program Manager"
    assert jobs[0].salary_max == 190000
    assert jobs[0].raw_payload["revision"] == 2
    assert jobs[0].normalized_payload["title"] == "Senior AI Program Manager"

    reset_engine()
    reset_settings_cache()
