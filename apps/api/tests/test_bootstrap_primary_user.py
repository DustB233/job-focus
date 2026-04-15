from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.repositories import JobFocusRepository
from app.services.bootstrap_primary_user import (
    PrimaryUserBootstrapInput,
    bootstrap_primary_user,
)


def build_bootstrap_input() -> PrimaryUserBootstrapInput:
    return PrimaryUserBootstrapInput(
        email="founder@example.com",
        password="super-secret-password",
        full_name="Jordan Rivera",
        headline="Staff product operator focused on AI systems and workflow automation.",
        location="San Francisco, CA",
        target_roles=["Product Operations", "AI Operations"],
        years_experience=9,
        seniority_level="staff",
        authorization_regions=["US"],
        preferred_locations=["Remote - US", "San Francisco, CA"],
        preferred_work_modes=["remote", "hybrid"],
        preferred_employment_types=["full_time"],
        desired_salary_min=180000,
        desired_salary_max=230000,
        auto_apply_enabled=False,
        auto_apply_min_score=90,
        resume_title="Jordan Rivera Resume",
        resume_file_name="jordan-rivera-resume.pdf",
        resume_summary="Led product operations, AI tooling rollouts, and cross-functional automation programs.",
        resume_skills=["Python", "SQL", "Automation", "Program Management"],
    )


def test_bootstrap_primary_user_creates_profile_preferences_and_resume(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "bootstrap_primary_user.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/15")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    from app.core.config import reset_settings_cache
    from app.db.session import create_all_tables, reset_engine, session_scope

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    payload = build_bootstrap_input()

    with session_scope() as session:
        result = bootstrap_primary_user(session, payload)

    with session_scope() as session:
        repository = JobFocusRepository(session)
        user = repository.get_primary_user()
        assert user is not None
        assert user.id == result.user_id
        assert user.email == payload.email
        assert user.profile is not None
        assert user.profile.full_name == payload.full_name
        preferences = repository.get_preferences_for_user(user.id)
        assert preferences is not None
        assert preferences.preferred_locations == payload.preferred_locations
        resume = repository.get_default_resume_for_user(user.id)
        assert resume is not None
        assert resume.title == payload.resume_title
        assert resume.skills == payload.resume_skills

    from app.main import app

    with TestClient(app) as client:
        profile_response = client.get("/api/profile/me")
        preferences_response = client.get("/api/profile/me/preferences")
        resume_response = client.get("/api/profile/me/resume")

    assert profile_response.status_code == 200
    assert preferences_response.status_code == 200
    assert resume_response.status_code == 200
    assert profile_response.json()["email"] == payload.email
    assert preferences_response.json()["preferredLocations"] == payload.preferred_locations
    assert resume_response.json()["fileName"] == payload.resume_file_name

    reset_engine()
    reset_settings_cache()


def test_bootstrap_primary_user_refuses_when_a_user_already_exists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "bootstrap_primary_user_existing.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/15")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    from app.core.config import reset_settings_cache
    from app.db.session import create_all_tables, reset_engine, session_scope

    reset_settings_cache()
    reset_engine()
    create_all_tables()

    payload = build_bootstrap_input()

    with session_scope() as session:
        bootstrap_primary_user(session, payload)

    with session_scope() as session:
        try:
            bootstrap_primary_user(session, payload)
        except RuntimeError as error:
            assert "zero users" in str(error)
        else:
            raise AssertionError("Expected bootstrap_primary_user to reject a non-empty system.")

    reset_engine()
    reset_settings_cache()
