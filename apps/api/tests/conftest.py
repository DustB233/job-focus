from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    database_path = tmp_path / "job_focus_api_test.db"
    return f"sqlite:///{database_path.as_posix()}"


@pytest.fixture
def seeded_database(monkeypatch: pytest.MonkeyPatch, database_url: str) -> str:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/15")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    from app.core.config import reset_settings_cache
    from app.db.session import create_all_tables, reset_engine, session_scope
    from app.services.seeding import seed_demo_data

    reset_settings_cache()
    reset_engine()
    create_all_tables()
    with session_scope() as session:
        seed_demo_data(session)

    yield database_url

    reset_engine()
    reset_settings_cache()


@pytest.fixture
def client(seeded_database: str) -> TestClient:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(seeded_database: str) -> Session:
    from app.db.session import session_scope

    with session_scope() as session:
        yield session
