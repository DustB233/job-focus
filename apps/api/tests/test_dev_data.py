import pytest

from app.core.config import Settings
from app.services.dev_data import ensure_dev_demo_data_allowed


def test_dev_demo_data_reset_allows_local_development_sqlite() -> None:
    settings = Settings(app_env="development", database_url="sqlite:///./job_focus.db")

    ensure_dev_demo_data_allowed(settings)


def test_dev_demo_data_reset_blocks_production() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://jobfocus:jobfocus@localhost:5432/jobfocus",
    )

    with pytest.raises(RuntimeError):
        ensure_dev_demo_data_allowed(settings)


def test_dev_demo_data_reset_blocks_non_local_databases() -> None:
    settings = Settings(
        app_env="development",
        database_url="postgresql+psycopg://jobfocus:jobfocus@db.example.com:5432/jobfocus",
    )

    with pytest.raises(RuntimeError):
        ensure_dev_demo_data_allowed(settings)
