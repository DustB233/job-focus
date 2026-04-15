from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageBarrier:
    code: str
    message: str


def detect_page_barriers(page) -> list[PageBarrier]:  # noqa: ANN001
    url = getattr(page, "url", "") or ""
    title = _safe_title(page)
    content = _safe_content(page)
    searchable = " ".join([url, title, content]).lower()

    barriers: list[PageBarrier] = []

    if any(token in searchable for token in ("captcha", "recaptcha", "hcaptcha", "verify you are human")):
        barriers.append(
            PageBarrier(
                code="captcha_detected",
                message="Captcha or human verification challenge detected.",
            )
        )

    if any(
        token in searchable
        for token in (
            "two-factor",
            "multi-factor",
            "one-time code",
            "authentication code",
            "authenticator app",
            "verification code",
        )
    ):
        barriers.append(
            PageBarrier(
                code="mfa_required",
                message="Multi-factor authentication challenge detected.",
            )
        )

    if (
        any(token in url.lower() for token in ("/login", "/signin", "/sign-in", "/auth"))
        or (
            "sign in" in searchable
            and any(token in searchable for token in ("password", "continue with", "log in"))
        )
    ):
        barriers.append(
            PageBarrier(
                code="login_required",
                message="The page appears to require an authenticated session.",
            )
        )

    if any(
        token in searchable
        for token in (
            "suspicious activity",
            "unusual traffic",
            "access denied",
            "security check",
            "checkpoint",
            "challenge required",
            "temporarily blocked",
        )
    ):
        barriers.append(
            PageBarrier(
                code="suspicious_page",
                message="The page appears to be blocked or under a security challenge.",
            )
        )

    return _dedupe_barriers(barriers)


def _safe_title(page) -> str:  # noqa: ANN001
    title_getter = getattr(page, "title", None)
    if callable(title_getter):
        try:
            return str(title_getter())
        except Exception:  # pragma: no cover - defensive fallback
            return ""
    return ""


def _safe_content(page) -> str:  # noqa: ANN001
    content_getter = getattr(page, "content", None)
    if callable(content_getter):
        try:
            return str(content_getter())
        except Exception:  # pragma: no cover - defensive fallback
            return ""
    return ""


def _dedupe_barriers(barriers: list[PageBarrier]) -> list[PageBarrier]:
    seen: set[str] = set()
    deduped: list[PageBarrier] = []
    for barrier in barriers:
        if barrier.code in seen:
            continue
        seen.add(barrier.code)
        deduped.append(barrier)
    return deduped
