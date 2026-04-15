from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db import normalize_database_url

LOCAL_APP_ENVS = {"development", "dev", "local", "test"}


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Job Focus API"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://jobfocus:jobfocus@localhost:5432/jobfocus"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    greenhouse_board_tokens: str = ""
    lever_site_names: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def greenhouse_boards(self) -> list[str]:
        return _split_csv(self.greenhouse_board_tokens)

    @property
    def lever_sites(self) -> list[str]:
        return _split_csv(self.lever_site_names)

    @property
    def normalized_database_url(self) -> str:
        return normalize_database_url(self.database_url)

    @property
    def is_local_environment(self) -> bool:
        return self.app_env.strip().lower() in LOCAL_APP_ENVS

    @property
    def is_local_database(self) -> bool:
        database_url = self.normalized_database_url

        if database_url.startswith("sqlite"):
            return True

        parsed = urlparse(database_url)
        hostname = (parsed.hostname or "").lower()
        return hostname in {"localhost", "127.0.0.1"}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
