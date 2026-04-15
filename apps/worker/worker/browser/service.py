from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.models import Application, ApplicationPacket, Job, User

from .auth import BrowserAuthSessionManager
from .detection import PageBarrier, detect_page_barriers
from .forms import GenericFormFiller
from .hooks import BrowserSiteAdapterHook, resolve_site_adapter_hook


@contextmanager
def default_browser_factory(headless: bool) -> Iterator[Any]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            yield browser
        finally:
            browser.close()


class PlaywrightBrowserAssistService:
    def __init__(
        self,
        *,
        auth_session_manager: BrowserAuthSessionManager,
        form_filler: GenericFormFiller | None = None,
        browser_factory=default_browser_factory,
        headless: bool = True,
        timeout_seconds: float = 15.0,
        resume_storage_dir: Path | str = "data/resumes",
        site_hook_resolver=resolve_site_adapter_hook,
    ) -> None:
        self.auth_session_manager = auth_session_manager
        self.form_filler = form_filler or GenericFormFiller()
        self.browser_factory = browser_factory
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.resume_storage_dir = Path(resume_storage_dir).expanduser().resolve()
        self.site_hook_resolver = site_hook_resolver

    def submit(
        self,
        *,
        application: Application,
        user: User,
        job: Job,
        packet: ApplicationPacket,
    ):
        from worker.execution import (
            ERROR_BROWSER_RUNTIME_UNAVAILABLE,
            ERROR_BROWSER_REVIEW_REQUIRED,
            ERROR_MANUAL_SUBMISSION_ONLY,
            ERROR_MISSING_APPLICATION_URL,
            ERROR_RESUME_FILE_MISSING,
            SubmissionFailure,
            SubmissionSuccess,
        )

        if job.application_url is None:
            return SubmissionFailure(
                outcome="failure",
                error_code=ERROR_MISSING_APPLICATION_URL,
                message="Application URL is missing.",
                retryable=False,
                payload={"source": job.job_source.slug.value},
            )

        hook = self.site_hook_resolver(job)
        if hook.manual_only:
            return SubmissionFailure(
                outcome="failure",
                error_code=ERROR_MANUAL_SUBMISSION_ONLY,
                message=f"{hook.name} never auto-submits applications.",
                retryable=False,
                payload={
                    "source": job.job_source.slug.value,
                    "host": hook.host_patterns[0] if hook.host_patterns else "",
                },
            )

        resume_path = self._resolve_resume_path(packet)
        if packet.resume_id and resume_path is None:
            return SubmissionFailure(
                outcome="failure",
                error_code=ERROR_RESUME_FILE_MISSING,
                message="The resume file required for browser upload could not be found.",
                retryable=False,
                payload={
                    "source": job.job_source.slug.value,
                    "expectedFileName": getattr(packet.resume, "file_name", None),
                },
            )

        state_key = hook.state_key(job)
        context = None
        try:
            with self.browser_factory(self.headless) as browser:
                context = browser.new_context(
                    **self.auth_session_manager.load_context_options(state_key)
                )
                page = context.new_page()
                page.goto(
                    job.application_url,
                    wait_until="domcontentloaded",
                    timeout=int(self.timeout_seconds * 1000),
                )
                initial_barriers = detect_page_barriers(page)
                if initial_barriers:
                    return self._review_required_failure(
                        initial_barriers,
                        source=job.job_source.slug.value,
                        message="Browser assist stopped because the target page requires manual attention.",
                    )

                fill_result = self.form_filler.fill_form(
                    page,
                    hook.build_fields(
                        user=user,
                        job=job,
                        packet=packet,
                        resume_path=resume_path,
                    ),
                )
                if fill_result.missing_required_fields or fill_result.issues:
                    reasons = list(fill_result.missing_required_fields) + list(fill_result.issues)
                    return SubmissionFailure(
                        outcome="failure",
                        error_code=ERROR_BROWSER_REVIEW_REQUIRED,
                        message="Browser assist could not confidently complete the required fields.",
                        retryable=False,
                        payload={
                            "source": job.job_source.slug.value,
                            "issues": reasons,
                        },
                    )

                post_fill_barriers = detect_page_barriers(page)
                if post_fill_barriers:
                    return self._review_required_failure(
                        post_fill_barriers,
                        source=job.job_source.slug.value,
                        message="Browser assist stopped after form fill because the page requires manual attention.",
                    )

                if not self.form_filler.submit_form(page, hook.submit_selectors):
                    return SubmissionFailure(
                        outcome="failure",
                        error_code=ERROR_BROWSER_REVIEW_REQUIRED,
                        message="Browser assist could not find a confident submit action.",
                        retryable=False,
                        payload={
                            "source": job.job_source.slug.value,
                            "issues": ["submit_button_not_found"],
                        },
                    )

                final_barriers = detect_page_barriers(page)
                if final_barriers:
                    return self._review_required_failure(
                        final_barriers,
                        source=job.job_source.slug.value,
                        message="Browser assist clicked submit but needs human review before the result can be trusted.",
                        possibly_submitted=True,
                    )

                if not self._looks_like_confirmation(page, hook):
                    return SubmissionFailure(
                        outcome="failure",
                        error_code=ERROR_BROWSER_REVIEW_REQUIRED,
                        message="Browser assist could not confirm the submission result with confidence.",
                        retryable=False,
                        payload={
                            "source": job.job_source.slug.value,
                            "issues": ["confirmation_not_detected"],
                            "possiblySubmitted": True,
                        },
                    )

                self.auth_session_manager.save_context_state(context, state_key)
                return SubmissionSuccess(
                    outcome="success",
                    confirmation_id=None,
                    confirmation_message="Browser-assisted submission confirmed from the page state.",
                    confirmation_url=getattr(page, "url", None),
                    submitted_at=self._utc_now(),
                    payload={
                        "provider": "browser_assist",
                        "stateKey": state_key,
                        "confirmationUrl": getattr(page, "url", None),
                    },
                )
        except ImportError as error:
            return SubmissionFailure(
                outcome="failure",
                error_code=ERROR_BROWSER_RUNTIME_UNAVAILABLE,
                message=f"Playwright is not installed: {error}",
                retryable=False,
                payload={"source": job.job_source.slug.value},
            )
        except Exception as error:  # pragma: no cover - defensive runtime fallback
            return SubmissionFailure(
                outcome="failure",
                error_code=ERROR_BROWSER_RUNTIME_UNAVAILABLE,
                message=f"Browser assist could not launch: {error}",
                retryable=True,
                payload={"source": job.job_source.slug.value},
            )
        finally:
            if context is not None:
                try:
                    self.auth_session_manager.save_context_state(context, state_key)
                except Exception:
                    pass
                close = getattr(context, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass

    def _resolve_resume_path(self, packet: ApplicationPacket) -> Path | None:
        resume = getattr(packet, "resume", None)
        file_name = getattr(resume, "file_name", None)
        if not file_name:
            return None

        candidate = self.resume_storage_dir / file_name
        if candidate.is_file():
            return candidate
        return None

    def _looks_like_confirmation(self, page, hook: BrowserSiteAdapterHook) -> bool:  # noqa: ANN001
        url = str(getattr(page, "url", "") or "").lower()
        if any(fragment in url for fragment in hook.success_url_fragments):
            return True

        title_getter = getattr(page, "title", None)
        title = str(title_getter()).lower() if callable(title_getter) else ""
        content_getter = getattr(page, "content", None)
        content = str(content_getter()).lower() if callable(content_getter) else ""
        searchable = " ".join([title, content])
        return any(keyword in searchable for keyword in hook.confirmation_keywords)

    def _review_required_failure(
        self,
        barriers: list[PageBarrier],
        *,
        source: str,
        message: str,
        possibly_submitted: bool = False,
    ):
        from worker.execution import SubmissionFailure

        return SubmissionFailure(
            outcome="failure",
            error_code=barriers[0].code if barriers else "browser_review_required",
            message=message,
            retryable=False,
            payload={
                "source": source,
                "issues": [barrier.code for barrier in barriers],
                "messages": [barrier.message for barrier in barriers],
                "possiblySubmitted": possibly_submitted,
            },
        )

    def _utc_now(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)


def build_playwright_browser_assist_service(
    *,
    auth_session_manager: BrowserAuthSessionManager,
    browser_factory=default_browser_factory,
    headless: bool = True,
    timeout_seconds: float = 15.0,
    resume_storage_dir: Path | str = "data/resumes",
) -> PlaywrightBrowserAssistService:
    return PlaywrightBrowserAssistService(
        auth_session_manager=auth_session_manager,
        browser_factory=browser_factory,
        headless=headless,
        timeout_seconds=timeout_seconds,
        resume_storage_dir=resume_storage_dir,
    )
