from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models import Application, ApplicationPacket, Job, User
from job_focus_shared import JobSource

ERROR_UNSUPPORTED_SOURCE = "unsupported_source"
ERROR_MISSING_APPLICATION_URL = "missing_application_url"
ERROR_INVALID_PACKET = "invalid_packet"
ERROR_DUPLICATE_SUBMISSION = "duplicate_submission"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_ATS_REJECTED = "ats_rejected"
ERROR_SERVER_ERROR = "server_error"
ERROR_NETWORK_ERROR = "network_error"
ERROR_BROWSER_FALLBACK_DISABLED = "browser_fallback_disabled"
ERROR_BROWSER_REVIEW_REQUIRED = "browser_review_required"
ERROR_BROWSER_RUNTIME_UNAVAILABLE = "browser_runtime_unavailable"
ERROR_LOGIN_REQUIRED = "login_required"
ERROR_MFA_REQUIRED = "mfa_required"
ERROR_CAPTCHA_DETECTED = "captcha_detected"
ERROR_SUSPICIOUS_PAGE = "suspicious_page"
ERROR_MANUAL_SUBMISSION_ONLY = "manual_submission_only"
ERROR_RESUME_FILE_MISSING = "resume_file_missing"
ERROR_UNKNOWN = "unknown_error"

WAITING_REVIEW_ERROR_CODES = {
    ERROR_BROWSER_REVIEW_REQUIRED,
    ERROR_LOGIN_REQUIRED,
    ERROR_MFA_REQUIRED,
    ERROR_CAPTCHA_DETECTED,
    ERROR_SUSPICIOUS_PAGE,
    ERROR_MANUAL_SUBMISSION_ONLY,
    ERROR_RESUME_FILE_MISSING,
}


@dataclass(frozen=True, slots=True)
class SubmissionTransportResponse:
    status_code: int
    payload: Any


@dataclass(frozen=True, slots=True)
class SubmissionSuccess:
    outcome: str
    confirmation_id: str | None
    confirmation_message: str | None
    confirmation_url: str | None
    submitted_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SubmissionFailure:
    outcome: str
    error_code: str
    message: str
    retryable: bool
    payload: dict[str, Any]


SubmissionResult = SubmissionSuccess | SubmissionFailure


class SubmissionTransport(Protocol):
    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> SubmissionTransportResponse:
        ...


class BrowserAutomationFallbackService(Protocol):
    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        ...


class DisabledBrowserAutomationFallbackService:
    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        return SubmissionFailure(
            outcome="failure",
            error_code=ERROR_BROWSER_FALLBACK_DISABLED,
            message="Browser automation fallback is disabled.",
            retryable=False,
            payload={"source": job.job_source.slug.value},
        )


class JsonSubmissionTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> SubmissionTransportResponse:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "JobFocusWorker/0.1",
                **(headers or {}),
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return SubmissionTransportResponse(
                    status_code=getattr(response, "status", 200),
                    payload=_decode_body(response.read()),
                )
        except HTTPError as error:
            return SubmissionTransportResponse(
                status_code=error.code,
                payload=_decode_body(error.read()),
            )
        except URLError as error:
            return SubmissionTransportResponse(
                status_code=0,
                payload={"detail": str(error.reason)},
            )


class ATSSubmissionAdapter(Protocol):
    source: JobSource
    name: str

    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        ...


class GreenhouseAutoApplyAdapter:
    source = JobSource.GREENHOUSE
    name = "Greenhouse Auto Apply"

    def __init__(self, transport: SubmissionTransport) -> None:
        self.transport = transport

    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        payload = _build_submission_payload(application, user, job, packet, provider="greenhouse")
        if isinstance(payload, SubmissionFailure):
            return payload

        response = self.transport.post_json(
            job.application_url or "",
            payload,
            headers={"X-JobFocus-Idempotency-Key": application.id},
        )
        return _normalize_submission_response(
            provider="greenhouse",
            response=response,
            confirmation_id_getter=lambda body: _read_string(body, "confirmation_id", "id"),
            confirmation_message_getter=lambda body: _read_string(body, "message", "status"),
            confirmation_url_getter=lambda body: _read_string(body, "confirmation_url"),
        )


class LeverAutoApplyAdapter:
    source = JobSource.LEVER
    name = "Lever Auto Apply"

    def __init__(self, transport: SubmissionTransport) -> None:
        self.transport = transport

    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        payload = _build_submission_payload(application, user, job, packet, provider="lever")
        if isinstance(payload, SubmissionFailure):
            return payload

        response = self.transport.post_json(
            job.application_url or "",
            payload,
            headers={"X-JobFocus-Idempotency-Key": application.id},
        )
        return _normalize_submission_response(
            provider="lever",
            response=response,
            confirmation_id_getter=lambda body: _read_string(body, "applicationId", "id"),
            confirmation_message_getter=lambda body: _read_string(body, "message", "status"),
            confirmation_url_getter=lambda body: _read_string(body, "hostedUrl"),
        )


class ApplicationExecutor:
    def __init__(
        self,
        *,
        adapters: dict[JobSource, ATSSubmissionAdapter],
        browser_fallback_enabled: bool = False,
        browser_fallback_service: BrowserAutomationFallbackService | None = None,
    ) -> None:
        self.adapters = adapters
        self.browser_fallback_enabled = browser_fallback_enabled
        self.browser_fallback_service = browser_fallback_service or DisabledBrowserAutomationFallbackService()

    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ) -> SubmissionResult:
        adapter = self.adapters.get(job.job_source.slug)
        if adapter is not None:
            return adapter.submit(application=application, user=user, job=job, packet=packet)

        if self.browser_fallback_enabled:
            return self.browser_fallback_service.submit(
                application=application,
                user=user,
                job=job,
                packet=packet,
            )

        return SubmissionFailure(
            outcome="failure",
            error_code=ERROR_UNSUPPORTED_SOURCE,
            message=f"No supported ATS executor is available for source {job.job_source.slug.value}.",
            retryable=False,
            payload={"source": job.job_source.slug.value},
        )


def build_application_executor(
    *,
    transport: SubmissionTransport | None = None,
    browser_fallback_enabled: bool = False,
    browser_assist_enabled: bool = False,
    browser_fallback_service: BrowserAutomationFallbackService | None = None,
    timeout_seconds: float = 10.0,
    browser_headless: bool = True,
    browser_auth_state_dir: Path | str | None = None,
    resume_storage_dir: Path | str = "data/resumes",
) -> ApplicationExecutor:
    effective_browser_enabled = browser_assist_enabled or browser_fallback_enabled
    submission_transport = transport or JsonSubmissionTransport(timeout_seconds=timeout_seconds)
    adapters: dict[JobSource, ATSSubmissionAdapter] = {
        JobSource.GREENHOUSE: GreenhouseAutoApplyAdapter(submission_transport),
        JobSource.LEVER: LeverAutoApplyAdapter(submission_transport),
    }
    if browser_fallback_service is None and effective_browser_enabled:
        from worker.browser.auth import BrowserAuthSessionManager
        from worker.browser.service import build_playwright_browser_assist_service

        auth_manager = BrowserAuthSessionManager(
            browser_auth_state_dir or (Path.home() / ".job-focus" / "browser-auth")
        )
        browser_fallback_service = build_playwright_browser_assist_service(
            auth_session_manager=auth_manager,
            headless=browser_headless,
            timeout_seconds=timeout_seconds,
            resume_storage_dir=resume_storage_dir,
        )

    return ApplicationExecutor(
        adapters=adapters,
        browser_fallback_enabled=effective_browser_enabled,
        browser_fallback_service=browser_fallback_service,
    )


def should_return_to_waiting_review(error_code: str) -> bool:
    return error_code in WAITING_REVIEW_ERROR_CODES


def _build_submission_payload(
    application: Application,
    user: User,
    job: Job,
    packet: ApplicationPacket,
    *,
    provider: str,
) -> dict[str, Any] | SubmissionFailure:
    profile = user.profile
    if job.application_url is None:
        return SubmissionFailure(
            outcome="failure",
            error_code=ERROR_MISSING_APPLICATION_URL,
            message="Application URL is missing.",
            retryable=False,
            payload={"provider": provider},
        )
    if profile is None:
        return SubmissionFailure(
            outcome="failure",
            error_code=ERROR_INVALID_PACKET,
            message="Structured user profile data is missing.",
            retryable=False,
            payload={"provider": provider, "missingFields": ["profile"]},
        )
    if packet.status.value == "needs_user_input" or packet.missing_fields:
        return SubmissionFailure(
            outcome="failure",
            error_code=ERROR_INVALID_PACKET,
            message="Packet still requires user input.",
            retryable=False,
            payload={"provider": provider, "missingFields": list(packet.missing_fields)},
        )

    return {
        "idempotencyKey": application.id,
        "jobId": job.external_job_id,
        "jobSource": job.job_source.slug.value,
        "applicant": {
            "email": user.email,
            "fullName": profile.full_name,
            "location": profile.location,
            "headline": profile.headline,
        },
        "applicationPacket": {
            "packetId": packet.id,
            "resumeVersion": packet.selected_resume_version,
            "tailoredResumeSummary": packet.tailored_resume_summary,
            "coverNote": packet.cover_note,
            "screeningAnswers": packet.screening_answers,
        },
    }


def _normalize_submission_response(
    *,
    provider: str,
    response: SubmissionTransportResponse,
    confirmation_id_getter: Callable[[Any], str | None],
    confirmation_message_getter: Callable[[Any], str | None],
    confirmation_url_getter: Callable[[Any], str | None],
) -> SubmissionResult:
    payload = response.payload if isinstance(response.payload, dict) else {"raw": response.payload}
    if 200 <= response.status_code < 300:
        return SubmissionSuccess(
            outcome="success",
            confirmation_id=confirmation_id_getter(payload),
            confirmation_message=confirmation_message_getter(payload),
            confirmation_url=confirmation_url_getter(payload),
            submitted_at=datetime.now(timezone.utc),
            payload={
                "provider": provider,
                "statusCode": response.status_code,
                "rawResponse": payload,
            },
        )

    normalized_error = _normalize_error(provider=provider, response=response)
    return SubmissionFailure(
        outcome="failure",
        error_code=normalized_error["errorCode"],
        message=normalized_error["message"],
        retryable=normalized_error["retryable"],
        payload=normalized_error,
    )


def _normalize_error(
    *,
    provider: str,
    response: SubmissionTransportResponse,
) -> dict[str, Any]:
    payload = response.payload if isinstance(response.payload, dict) else {"raw": response.payload}
    message = _read_string(payload, "message", "error", "detail") or "Submission failed."
    message_lower = message.lower()

    if response.status_code == 0:
        error_code = ERROR_NETWORK_ERROR
        retryable = True
    elif response.status_code == 409 or "already applied" in message_lower or "duplicate" in message_lower:
        error_code = ERROR_DUPLICATE_SUBMISSION
        retryable = False
    elif response.status_code == 422:
        error_code = ERROR_INVALID_PACKET
        retryable = False
    elif response.status_code == 429:
        error_code = ERROR_RATE_LIMITED
        retryable = True
    elif 400 <= response.status_code < 500:
        error_code = ERROR_ATS_REJECTED
        retryable = False
    elif response.status_code >= 500:
        error_code = ERROR_SERVER_ERROR
        retryable = True
    else:
        error_code = ERROR_UNKNOWN
        retryable = False

    return {
        "provider": provider,
        "statusCode": response.status_code,
        "errorCode": error_code,
        "message": message,
        "retryable": retryable,
        "rawResponse": payload,
    }


def _read_string(body: Any, *keys: str) -> str | None:
    if not isinstance(body, dict):
        return None
    for key in keys:
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _decode_body(body: bytes) -> Any:
    if not body:
        return {}
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}
