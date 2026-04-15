from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] == "ok"


def test_profile_and_resume_endpoints(client: TestClient) -> None:
    profile_response = client.get("/api/profile/me")
    preferences_response = client.get("/api/profile/me/preferences")
    resume_response = client.get("/api/profile/me/resume")

    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "demo@jobfocus.dev"
    assert preferences_response.status_code == 200
    assert preferences_response.json()["preferredLocations"][0] == "Remote - US"
    assert resume_response.status_code == 200
    assert resume_response.json()["fileName"] == "avery-collins-resume.pdf"


def test_jobs_endpoint_returns_seeded_roles(client: TestClient) -> None:
    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_apply_endpoint_is_idempotent(client: TestClient) -> None:
    jobs = client.get("/api/jobs").json()
    target_job_id = jobs[1]["id"]

    first = client.post(f"/api/applications/{target_job_id}/apply")
    second = client.post(f"/api/applications/{target_job_id}/apply")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_tracker_overview_counts_seeded_records(client: TestClient) -> None:
    response = client.get("/api/tracker/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["userCount"] == 1
    assert payload["jobCount"] == 3
    assert payload["applicationCount"] == 3
    assert payload["configuredLiveSourceCount"] == 0


def test_tracker_distinguishes_configured_sources_before_first_ingest(
    monkeypatch, database_url: str
) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/15")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("GREENHOUSE_BOARD_TOKENS", "northstar")
    monkeypatch.setenv("LEVER_SITE_NAMES", "")

    from app.core.config import reset_settings_cache
    from app.db.session import create_all_tables, reset_engine, session_scope
    from app.services.tracker import build_source_health, build_tracker_overview

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    with session_scope() as session:
        overview = build_tracker_overview(session)
        source_health = build_source_health(session)

    assert overview.configured_live_source_count == 1
    assert len(source_health) == 1
    assert source_health[0].source.value == "greenhouse"
    assert source_health[0].job_count == 0
    assert "configured" in source_health[0].note.lower()

    reset_engine()
    reset_settings_cache()


def test_source_health_endpoint_returns_all_configured_sources(client: TestClient) -> None:
    response = client.get("/api/tracker/sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert payload[0]["displayName"] == "Ashby"


def test_review_endpoint_moves_waiting_review_into_submitting(client: TestClient) -> None:
    applications = client.get("/api/applications").json()
    waiting_review = next(
        application for application in applications if application["status"] == "waiting_review"
    )

    response = client.post(
        f"/api/applications/{waiting_review['id']}/review",
        json={"action": "approve", "note": "Approved in API test."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "submitting"
    assert payload["events"][-1]["toStatus"] == "submitting"
