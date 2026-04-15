from __future__ import annotations

import os

import uvicorn

from app.core.config import Settings, get_settings


def resolve_runtime_host(settings: Settings | None = None) -> str:
    resolved_settings = settings or get_settings()
    return resolved_settings.api_host


def resolve_runtime_port(
    settings: Settings | None = None,
    *,
    port_override: str | None = None,
) -> int:
    resolved_settings = settings or get_settings()
    raw_port = port_override if port_override is not None else os.getenv("PORT")

    if raw_port is None or not raw_port.strip():
        return resolved_settings.api_port

    try:
        return int(raw_port)
    except ValueError as error:  # pragma: no cover - defensive runtime validation
        raise ValueError(f"Invalid PORT value: {raw_port!r}") from error


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=resolve_runtime_host(settings),
        port=resolve_runtime_port(settings),
        reload=False,
    )


if __name__ == "__main__":
    main()
