from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import reset_settings_cache
from app.db.session import create_all_tables, reset_engine, session_scope
from app.repositories import JobFocusRepository
from app.services.bootstrap_primary_user import (
    PrimaryUserBootstrapInput,
    bootstrap_primary_user,
)
from job_focus_shared import (
    ApplicationStatus,
    DiscoveredJobDTO,
    EmploymentType,
    JobSource,
    WorkMode,
)

from worker.config import WorkerSettings
from worker.tasks.pipeline import generate_packets, score_jobs


def build_bootstrap_input() -> PrimaryUserBootstrapInput:
    return PrimaryUserBootstrapInput(
        email="founder@example.com",
        password="super-secret-password",
        full_name="Jordan Rivera",
        headline="Staff product operator focused on AI systems and workflow automation.",
        location="San Francisco, CA",
        target_roles=["AI Operations", "Product Operations"],
        years_experience=9,
        seniority_level="staff",
        authorization_regions=["US"],
        preferred_locations=["Remote - US", "San Francisco, CA"],
        preferred_work_modes=["remote", "hybrid"],
        preferred_employment_types=["full_time"],
        desired_salary_min=180000,
        desired_salary_max=230000,
        auto_apply_enabled=False,
        auto_apply_min_score=80,
        resume_title="Jordan Rivera Resume",
        resume_file_name="jordan-rivera-resume.pdf",
        resume_summary="Led AI operations, automation tooling, and product execution systems.",
        resume_skills=["Python", "SQL", "Automation", "Program Management"],
    )


class DummyTracker:
    def __init__(self) -> None:
        self.events: dict[str, str] = {}

    def record(self, task_name: str, run_at) -> None:  # noqa: ANN001
        self.events[task_name] = run_at.isoformat()


def test_bootstrapped_primary_user_unblocks_scoring_and_packet_generation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "job_focus_bootstrap_pipeline.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        bootstrap_primary_user(session, build_bootstrap_input())
        repository = JobFocusRepository(session)
        source = repository.get_or_create_job_source(
            slug=JobSource.GREENHOUSE,
            external_identifier="acme",
            display_name="Greenhouse / Acme",
            base_url="https://boards-api.greenhouse.io/v1/boards/acme",
        )
        repository.upsert_discovered_job(
            source=source,
            discovered_job=DiscoveredJobDTO(
                source=JobSource.GREENHOUSE,
                external_job_id="acme-ai-ops-1",
                company="Acme AI",
                title="AI Operations Lead",
                location="Remote - US",
                work_mode=WorkMode.REMOTE,
                employment_type=EmploymentType.FULL_TIME,
                salary_min=190000,
                salary_max=220000,
                description="Drive automation, Python tooling, and program execution for AI operations.",
                application_url="https://boards.greenhouse.io/acme/jobs/12345",
                seniority_level="staff",
                authorization_requirement="US work authorization required",
                posted_at=datetime(2026, 4, 15, 8, 0, 0, tzinfo=timezone.utc),
                raw_payload={"fixture": True},
            ),
        )
        session.commit()

    tracker = DummyTracker()
    settings = WorkerSettings(
        database_url=database_url,
        redis_url="redis://localhost:6391/15",
        auto_apply_min_score=80,
    )

    with session_scope() as session:
        score_result = score_jobs(session, tracker)
        packet_result = generate_packets(session, tracker, settings)

    with session_scope() as session:
        repository = JobFocusRepository(session)
        user = repository.get_primary_user()
        assert user is not None
        matches = repository.list_matches_for_user(user.id)
        applications = repository.list_applications_for_user(user.id)

    assert score_result["created_matches"] == 1
    assert packet_result["ready_packets"] == 1
    assert len(matches) == 1
    assert matches[0].match_score >= settings.auto_apply_min_score
    assert len(applications) == 1
    assert applications[0].status == ApplicationStatus.WAITING_REVIEW
    assert applications[0].current_packet is not None
    assert applications[0].current_packet.resume_id is not None
    assert {"score", "packet"} <= tracker.events.keys()

    reset_engine()
    reset_settings_cache()
