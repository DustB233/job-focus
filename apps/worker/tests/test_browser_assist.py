from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from job_focus_shared import JobSource

from worker.browser.auth import BrowserAuthSessionManager
from worker.browser.forms import BrowserFormField, GenericFormFiller
from worker.browser.service import PlaywrightBrowserAssistService
from worker.execution import (
    ERROR_CAPTCHA_DETECTED,
    ERROR_MANUAL_SUBMISSION_ONLY,
    SubmissionSuccess,
)


class FakeLocator:
    def __init__(self, page: "FakePage", selector: str, *, visible: bool = True) -> None:
        self.page = page
        self.selector = selector
        self.visible = visible

    def count(self) -> int:
        return 1 if self.visible else 0

    def fill(self, value: str) -> None:
        self.page.filled[self.selector] = value

    def set_input_files(self, path: str) -> None:
        self.page.uploads[self.selector] = path

    def check(self) -> None:
        self.page.checked[self.selector] = True

    def click(self) -> None:
        self.page.clicked.append(self.selector)
        if self.page.after_submit is not None:
            self.page.after_submit(self.page)

    def is_visible(self) -> bool:
        return self.visible


class FakePage:
    def __init__(
        self,
        *,
        url: str,
        title: str = "Apply",
        content: str = "<form></form>",
        locators: dict[str, FakeLocator] | None = None,
        labels: dict[str, FakeLocator] | None = None,
        after_submit=None,
    ) -> None:
        self.url = url
        self._title = title
        self._content = content
        self._locators = locators or {}
        self._labels = labels or {}
        self.after_submit = after_submit
        self.filled: dict[str, str] = {}
        self.uploads: dict[str, str] = {}
        self.checked: dict[str, bool] = {}
        self.clicked: list[str] = []

    def goto(self, url: str, **_: object) -> None:
        self.url = url

    def locator(self, selector: str) -> FakeLocator:
        return self._locators.get(selector, FakeLocator(self, selector, visible=False))

    def get_by_label(self, label: str, exact: bool = False) -> FakeLocator:  # noqa: ARG002
        return self._labels.get(label.lower(), FakeLocator(self, label, visible=False))

    def wait_for_load_state(self, state: str) -> None:  # noqa: ARG002
        return None

    def title(self) -> str:
        return self._title

    def content(self) -> str:
        return self._content


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.storage_state_calls: list[str] = []

    def new_page(self) -> FakePage:
        return self.page

    def storage_state(self, *, path: str) -> None:
        Path(path).write_text('{"cookies":[],"origins":[]}', encoding="utf-8")
        self.storage_state_calls.append(path)

    def close(self) -> None:
        return None


class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.context_kwargs: dict[str, object] | None = None
        self.context = FakeContext(page)

    def new_context(self, **kwargs: object) -> FakeContext:
        self.context_kwargs = kwargs
        return self.context


def build_test_user():
    return SimpleNamespace(
        email="demo@jobfocus.dev",
        profile=SimpleNamespace(
            full_name="Avery Collins",
            headline="Operations leader",
            location="Seattle, WA",
        ),
    )


def build_test_packet(*, file_name: str | None = None):
    resume = SimpleNamespace(file_name=file_name) if file_name else None
    return SimpleNamespace(
        resume_id="resume-1" if file_name else None,
        resume=resume,
        cover_note="Cover note based on approved profile data.",
        tailored_resume_summary="Tailored summary for the role.",
        screening_answers={"work_authorization": "Authorized to work in the United States."},
    )


def build_test_job(url: str):
    return SimpleNamespace(
        application_url=url,
        job_source=SimpleNamespace(slug=JobSource.MANUAL),
    )


def test_auth_session_manager_saves_state_under_a_sanitized_secure_path(tmp_path: Path) -> None:
    manager = BrowserAuthSessionManager(tmp_path / "auth-state")
    context = FakeContext(FakePage(url="https://example.com/apply"))
    state_key = manager.state_key_for_url(
        source=JobSource.MANUAL,
        url="https://example.com/login?continue=%2Fapply",
    )

    saved_path = manager.save_context_state(context, state_key)

    assert saved_path.is_file()
    assert "manual-example.com" in saved_path.name
    assert manager.load_context_options(state_key)["storage_state"] == str(saved_path)


def test_generic_form_filler_handles_text_fields_and_file_uploads(tmp_path: Path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_text("fake pdf bytes", encoding="utf-8")
    page = FakePage(
        url="https://example.com/apply",
        locators={
            'input[name="email"]': FakeLocator(None, 'input[name="email"]'),
            'input[type="file"][accept*="pdf"]': FakeLocator(
                None,
                'input[type="file"][accept*="pdf"]',
            ),
        },
        labels={
            "full name": FakeLocator(None, "full name"),
        },
    )
    for locator in list(page._locators.values()) + list(page._labels.values()):
        locator.page = page

    filler = GenericFormFiller()
    result = filler.fill_form(
        page,
        [
            BrowserFormField(
                key="full_name",
                value="Avery Collins",
                label_hints=("full name",),
                required=True,
            ),
            BrowserFormField(
                key="email",
                value="demo@jobfocus.dev",
                name_hints=("email",),
                required=True,
            ),
            BrowserFormField(
                key="resume_upload",
                value=resume_path,
                field_type="file",
                selectors=('input[type="file"][accept*="pdf"]',),
                required=True,
            ),
        ],
    )

    assert result.missing_required_fields == []
    assert page.filled["full name"] == "Avery Collins"
    assert page.filled['input[name="email"]'] == "demo@jobfocus.dev"
    assert page.uploads['input[type="file"][accept*="pdf"]'] == str(resume_path)


def test_browser_assist_marks_review_required_when_captcha_is_detected(tmp_path: Path) -> None:
    auth_manager = BrowserAuthSessionManager(tmp_path / "auth-state")
    page = FakePage(
        url="https://example.com/apply",
        content="<html><body>Please verify you are human with captcha.</body></html>",
    )
    browser = FakeBrowser(page)

    @contextmanager
    def fake_browser_factory(headless: bool):  # noqa: ARG001
        yield browser

    service = PlaywrightBrowserAssistService(
        auth_session_manager=auth_manager,
        browser_factory=fake_browser_factory,
        resume_storage_dir=tmp_path,
    )

    result = service.submit(
        application=SimpleNamespace(id="application-1"),
        user=build_test_user(),
        job=build_test_job("https://example.com/apply"),
        packet=build_test_packet(),
    )

    assert result.error_code == ERROR_CAPTCHA_DETECTED
    assert "captcha_detected" in result.payload["issues"]


def test_browser_assist_never_submits_linkedin_or_handshake(tmp_path: Path) -> None:
    auth_manager = BrowserAuthSessionManager(tmp_path / "auth-state")
    service = PlaywrightBrowserAssistService(
        auth_session_manager=auth_manager,
        resume_storage_dir=tmp_path,
    )

    result = service.submit(
        application=SimpleNamespace(id="application-1"),
        user=build_test_user(),
        job=build_test_job("https://www.linkedin.com/jobs/view/1234567890"),
        packet=build_test_packet(),
    )

    assert result.error_code == ERROR_MANUAL_SUBMISSION_ONLY


def test_browser_assist_can_confirm_a_successful_generic_submission(tmp_path: Path) -> None:
    auth_manager = BrowserAuthSessionManager(tmp_path / "auth-state")
    resume_dir = tmp_path / "resumes"
    resume_dir.mkdir()
    resume_path = resume_dir / "avery-collins-resume.pdf"
    resume_path.write_text("fake pdf bytes", encoding="utf-8")

    def after_submit(page: FakePage) -> None:
        page.url = "https://example.com/application/submitted"
        page._content = "<html><body>Thank you for applying.</body></html>"

    page = FakePage(
        url="https://example.com/apply",
        locators={},
        labels={"full name": FakeLocator(None, "full name")},
        after_submit=after_submit,
    )
    page._locators.update(
        {
            'input[name="email"]': FakeLocator(page, 'input[name="email"]'),
            'input[type="file"][accept*="pdf"]': FakeLocator(
                page,
                'input[type="file"][accept*="pdf"]',
            ),
            'button[type="submit"]': FakeLocator(page, 'button[type="submit"]'),
        }
    )
    page._labels["full name"] = FakeLocator(page, "full name")
    browser = FakeBrowser(page)

    @contextmanager
    def fake_browser_factory(headless: bool):  # noqa: ARG001
        yield browser

    service = PlaywrightBrowserAssistService(
        auth_session_manager=auth_manager,
        browser_factory=fake_browser_factory,
        resume_storage_dir=resume_dir,
    )

    result = service.submit(
        application=SimpleNamespace(id="application-1"),
        user=build_test_user(),
        job=build_test_job("https://example.com/apply"),
        packet=build_test_packet(file_name="avery-collins-resume.pdf"),
    )

    assert isinstance(result, SubmissionSuccess)
    assert result.confirmation_url == "https://example.com/application/submitted"
    saved_states = list((tmp_path / "auth-state").glob("*.json"))
    assert saved_states
