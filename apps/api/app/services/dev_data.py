from __future__ import annotations

from app.core.config import Settings


def ensure_dev_demo_data_allowed(settings: Settings) -> None:
    if not settings.is_local_environment:
        raise RuntimeError(
            "Demo data reset is disabled outside local development and test environments."
        )

    if not settings.is_local_database:
        raise RuntimeError(
            "Demo data reset is only allowed against a local SQLite or localhost database URL."
        )
