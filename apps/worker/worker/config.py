from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    app_name: str = "Job Focus Worker"
    database_url: str = "postgresql+psycopg://jobfocus:jobfocus@localhost:5432/jobfocus"
    redis_url: str = "redis://localhost:6379/0"
    ingest_interval_minutes: int = 30
    score_interval_minutes: int = 15
    packet_interval_minutes: int = 20
    apply_interval_minutes: int = 25
    auto_apply_min_score: int = 85
    greenhouse_board_tokens: str = ""
    lever_site_names: str = ""
    source_request_timeout_seconds: float = 10.0
    source_request_interval_seconds: float = 1.0
    source_max_retries: int = 3
    source_retry_backoff_seconds: float = 1.0
    ats_apply_timeout_seconds: float = 10.0
    browser_assist_enabled: bool = False
    browser_fallback_enabled: bool = False
    browser_headless: bool = True
    browser_auth_state_dir: str = ""
    browser_resume_storage_dir: str = "data/resumes"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def greenhouse_boards(self) -> list[str]:
        return _split_csv(self.greenhouse_board_tokens)

    @property
    def lever_sites(self) -> list[str]:
        return _split_csv(self.lever_site_names)

    @property
    def browser_automation_enabled(self) -> bool:
        return self.browser_assist_enabled or self.browser_fallback_enabled

    @property
    def resolved_browser_auth_state_dir(self) -> Path:
        if self.browser_auth_state_dir:
            return Path(self.browser_auth_state_dir).expanduser().resolve()
        return (Path.home() / ".job-focus" / "browser-auth").resolve()

    @property
    def resolved_browser_resume_storage_dir(self) -> Path:
        return Path(self.browser_resume_storage_dir).expanduser().resolve()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
