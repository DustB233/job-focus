from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from job_focus_shared import JobSource

STATE_KEY_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


class StorageStateContext(Protocol):
    def storage_state(self, *, path: str) -> None: ...


def sanitize_state_key(value: str) -> str:
    cleaned = STATE_KEY_PATTERN.sub("-", value.strip()).strip(".-")
    return cleaned or "default"


class BrowserAuthSessionManager:
    def __init__(self, storage_dir: Path | str) -> None:
        self.storage_dir = Path(storage_dir).expanduser().resolve()
        self._ensure_secure_directory()

    def state_key_for_url(self, *, source: JobSource, url: str | None) -> str:
        hostname = urlparse(url or "").hostname or "generic"
        return sanitize_state_key(f"{source.value}-{hostname}")

    def resolve_state_path(self, state_key: str) -> Path:
        return self.storage_dir / f"{sanitize_state_key(state_key)}.json"

    def load_context_options(self, state_key: str) -> dict[str, str]:
        path = self.resolve_state_path(state_key)
        if not path.is_file():
            return {}
        self._ensure_secure_file(path)
        return {"storage_state": str(path)}

    def save_context_state(self, context: StorageStateContext, state_key: str) -> Path:
        path = self.resolve_state_path(state_key)
        self._ensure_secure_directory()
        context.storage_state(path=str(path))
        self._ensure_secure_file(path)
        return path

    def _ensure_secure_directory(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.storage_dir, 0o700)
        except OSError:
            # Best effort only. Windows ignores POSIX permission bits.
            pass

    def _ensure_secure_file(self, path: Path) -> None:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
