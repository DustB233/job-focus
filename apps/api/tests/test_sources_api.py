from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_list_sources_returns_many_registry_rows_with_serialized_counts(
    client: TestClient,
    db_session: Session,
) -> None:
    from datetime import datetime, timezone

    from app.models import Job, JobSourceConfig
    from job_focus_shared import EmploymentType, JobSource, WorkMode

    now = datetime.now(timezone.utc)
    for index in range(30):
        slug = JobSource.LEVER if index % 2 else JobSource.GREENHOUSE
        identifier = f"production-source-{index}"
        source = JobSourceConfig(
            slug=slug,
            external_identifier=identifier,
            display_name=f"{slug.value.title()} / Production Source {index}",
            base_url=f"https://example.com/{identifier}",
            is_active=True,
            last_sync_started_at=now,
            last_sync_completed_at=now,
            last_successful_sync_at=now,
            last_fetched_job_count=4,
            last_created_job_count=4,
            last_updated_job_count=0,
        )
        db_session.add(source)
        db_session.flush()
        for job_index in range(4):
            db_session.add(
                Job(
                    job_source_id=source.id,
                    external_job_id=f"{identifier}:{job_index}",
                    company=f"Company {index}",
                    title=f"Role {job_index}",
                    location="Remote - US",
                    work_mode=WorkMode.REMOTE,
                    employment_type=EmploymentType.FULL_TIME,
                    salary_min=100000,
                    salary_max=150000,
                    description="Production-shaped job row.",
                    application_url=f"https://example.com/{identifier}/{job_index}",
                    seniority_level="senior",
                    authorization_requirement="US work authorization required",
                    raw_payload={},
                    normalized_payload={},
                    posted_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
    db_session.commit()

    response = client.get("/api/sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 34
    production_source = next(
        source for source in payload if source["externalIdentifier"] == "production-source-0"
    )
    assert production_source["trackedJobCount"] == 4
    assert production_source["lastFetchedJobCount"] == 4
    assert production_source["status"] == "healthy"
    assert "tracked_job_count" not in production_source
    assert "last_fetched_job_count" not in production_source


def test_list_sources_returns_registry_rows(client: TestClient) -> None:
    response = client.get("/api/sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 4
    assert any(
        source["source"] == "greenhouse" and source["externalIdentifier"] == "northstar"
        for source in payload
    )


def test_create_enable_disable_and_sync_source(client: TestClient) -> None:
    create_response = client.post(
        "/api/sources",
        json={
            "source": "lever",
            "externalIdentifier": "atlas",
            "displayName": "Lever / Atlas",
            "isActive": True,
        },
    )

    assert create_response.status_code == 201
    created_source = create_response.json()
    assert created_source["source"] == "lever"
    assert created_source["externalIdentifier"] == "atlas"
    assert created_source["isActive"] is True

    disable_response = client.post(f"/api/sources/{created_source['id']}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["isActive"] is False

    enable_response = client.post(f"/api/sources/{created_source['id']}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["isActive"] is True

    sync_response = client.post(f"/api/sources/{created_source['id']}/sync")
    assert sync_response.status_code == 200
    assert sync_response.json()["lastSyncRequestedAt"] is not None


def test_create_source_rejects_manual_only_provider(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        json={
            "source": "manual",
            "externalIdentifier": "linkedin",
            "displayName": "LinkedIn Manual Link",
            "isActive": True,
        },
    )

    assert response.status_code == 422
