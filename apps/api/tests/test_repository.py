from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Application, ApplicationEvent, Job
from app.repositories import (
    DuplicateApplicationError,
    InvalidApplicationTransitionError,
    JobFocusRepository,
)
from job_focus_shared import (
    ApplicationStatus,
    DiscoveredJobDTO,
    EmploymentType,
    JobSource,
    PacketStatus,
    WorkMode,
)


def create_test_job(
    repository: JobFocusRepository,
    *,
    external_job_id: str,
    title: str = "Test Operations Role",
) -> Job:
    source = repository.get_or_create_job_source(
        slug=JobSource.MANUAL,
        display_name="Manual Link",
    )
    job, _ = repository.upsert_discovered_job(
        source=source,
        discovered_job=DiscoveredJobDTO(
            source=JobSource.MANUAL,
            external_job_id=external_job_id,
            company="Test Company",
            title=title,
            location="Remote - US",
            work_mode=WorkMode.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            salary_min=120000,
            salary_max=140000,
            description="Repository test job.",
            application_url="https://example.com/jobs/test",
            seniority_level="senior",
            authorization_requirement="US work authorization required",
            posted_at=datetime(2026, 4, 13, 8, 0, 0, tzinfo=timezone.utc),
            raw_payload={"fixture": True, "externalJobId": external_job_id},
        ),
    )
    return job


def test_application_state_machine_happy_path(db_session: Session) -> None:
    repository = JobFocusRepository(db_session)
    user = repository.get_primary_user()
    assert user is not None

    job = create_test_job(repository, external_job_id="repo-state-machine")
    resume = repository.get_default_resume_for_user(user.id)
    assert resume is not None

    application = repository.create_application(
        user=user,
        job=job,
        notes="Created for transition testing.",
        actor="test",
    )

    application = repository.transition_application_status(
        application,
        ApplicationStatus.SHORTLISTED,
        actor="test",
        note="Shortlisted in test.",
    )

    packet = repository.create_application_packet(
        user=user,
        job=job,
        resume=resume,
        status=PacketStatus.DRAFT_READY,
        tailored_resume_summary="Tailored summary",
        cover_note="Cover note draft",
        screening_answers={"authorization": "Authorized"},
        missing_fields=[],
    )

    application = repository.transition_application_status(
        application,
        ApplicationStatus.DRAFT_READY,
        actor="test",
        note="Draft packet attached.",
        current_packet=packet,
    )
    application = repository.transition_application_status(
        application,
        ApplicationStatus.WAITING_REVIEW,
        actor="test",
        note="Queued for review.",
        current_packet=packet,
    )
    application = repository.transition_application_status(
        application,
        ApplicationStatus.SUBMITTING,
        actor="test",
        note="Submitting.",
    )
    application = repository.transition_application_status(
        application,
        ApplicationStatus.SUBMITTED,
        actor="test",
        note="Submitted successfully.",
    )

    refreshed = repository.get_application_for_job(user.id, job.id)
    assert refreshed is not None
    assert refreshed.status == ApplicationStatus.SUBMITTED
    assert refreshed.current_packet_id == packet.id
    assert refreshed.submitted_at is not None

    event_count = db_session.scalar(
        select(func.count(ApplicationEvent.id)).where(ApplicationEvent.application_id == refreshed.id)
    )
    assert event_count == 6


def test_invalid_transition_is_rejected(db_session: Session) -> None:
    repository = JobFocusRepository(db_session)
    user = repository.get_primary_user()
    assert user is not None

    job = create_test_job(repository, external_job_id="repo-invalid-transition")
    application = repository.create_application(user=user, job=job, actor="test")

    try:
        repository.transition_application_status(
            application,
            ApplicationStatus.SUBMITTED,
            actor="test",
            note="This should not be allowed.",
        )
    except InvalidApplicationTransitionError:
        pass
    else:
        raise AssertionError("Expected InvalidApplicationTransitionError to be raised.")


def test_duplicate_prevention_blocks_second_application(db_session: Session) -> None:
    repository = JobFocusRepository(db_session)
    user = repository.get_primary_user()
    assert user is not None

    job = create_test_job(repository, external_job_id="repo-duplicate-prevention")
    repository.create_application(user=user, job=job, actor="test")

    before_count = db_session.scalar(select(func.count(Application.id)))

    try:
        repository.create_application(user=user, job=job, actor="test")
    except DuplicateApplicationError as error:
        assert error.application.job_id == job.id
    else:
        raise AssertionError("Expected DuplicateApplicationError to be raised.")

    after_count = db_session.scalar(select(func.count(Application.id)))
    assert before_count == after_count


def test_upsert_discovered_job_deduplicates_source_external_id(db_session: Session) -> None:
    repository = JobFocusRepository(db_session)
    source = repository.get_or_create_job_source(
        slug=JobSource.GREENHOUSE,
        display_name="Greenhouse",
        base_url="https://boards-api.greenhouse.io/v1/boards",
    )
    discovered_job = DiscoveredJobDTO(
        source=JobSource.GREENHOUSE,
        external_job_id="northstar:12345",
        company="Northstar Labs",
        title="AI Program Manager",
        location="Remote - US",
        work_mode=WorkMode.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        salary_min=150000,
        salary_max=180000,
        description="Lead AI delivery systems.",
        application_url="https://boards.greenhouse.io/northstar/jobs/12345",
        seniority_level="senior",
        authorization_requirement="Valid work authorization required.",
        posted_at=datetime(2026, 4, 13, 8, 0, 0, tzinfo=timezone.utc),
        raw_payload={"revision": 1},
    )

    job, created = repository.upsert_discovered_job(source=source, discovered_job=discovered_job)
    assert created is True

    refreshed_job, created = repository.upsert_discovered_job(
        source=source,
        discovered_job=discovered_job.model_copy(
            update={
                "title": "Senior AI Program Manager",
                "salary_max": 190000,
                "raw_payload": {"revision": 2},
            }
        ),
    )

    job_count = db_session.scalar(
        select(func.count(Job.id)).where(
            Job.job_source_id == source.id,
            Job.external_job_id == discovered_job.external_job_id,
        )
    )

    assert created is False
    assert job_count == 1
    assert refreshed_job.id == job.id
    assert refreshed_job.title == "Senior AI Program Manager"
    assert refreshed_job.salary_max == 190000
    assert refreshed_job.raw_payload["revision"] == 2
    assert refreshed_job.normalized_payload["title"] == "Senior AI Program Manager"
