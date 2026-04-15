from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.models import ApplicationPacket, Job, User
from job_focus_shared import JobSource

from .forms import BrowserFormField

SCREENING_LABEL_HINTS = {
    "work_authorization": (
        "work authorization",
        "authorized to work",
        "require sponsorship",
        "visa sponsorship",
    ),
    "years_experience": ("years of experience", "experience"),
    "location_flexibility": ("location", "where are you based", "are you open to relocate"),
    "work_mode_preference": ("work mode", "remote", "hybrid", "onsite"),
}


@dataclass(frozen=True, slots=True)
class BrowserSiteAdapterHook:
    name: str
    host_patterns: tuple[str, ...]
    submit_selectors: tuple[str, ...]
    confirmation_keywords: tuple[str, ...]
    success_url_fragments: tuple[str, ...] = ()
    manual_only: bool = False

    def matches(self, job: Job) -> bool:
        hostname = (urlparse(job.application_url or "").hostname or "").lower()
        return any(hostname.endswith(pattern) for pattern in self.host_patterns)

    def build_fields(
        self,
        *,
        user: User,
        job: Job,
        packet: ApplicationPacket,
        resume_path: Path | None,
    ) -> list[BrowserFormField]:
        profile = user.profile
        if profile is None:
            return []

        first_name, last_name = _split_name(profile.full_name)
        fields: list[BrowserFormField] = [
            BrowserFormField(
                key="first_name",
                value=first_name,
                selectors=("#first_name", 'input[name="first_name"]'),
                label_hints=("first name",),
                name_hints=("first_name", "firstname", "firstName"),
            ),
            BrowserFormField(
                key="last_name",
                value=last_name,
                selectors=("#last_name", 'input[name="last_name"]'),
                label_hints=("last name",),
                name_hints=("last_name", "lastname", "lastName"),
            ),
            BrowserFormField(
                key="full_name",
                value=profile.full_name,
                selectors=('#candidate_name', 'input[name="name"]'),
                label_hints=("full name", "name"),
                name_hints=("full_name", "fullName", "name", "candidate_name"),
                required=True,
            ),
            BrowserFormField(
                key="email",
                value=user.email,
                selectors=("#email", 'input[name="email"]'),
                label_hints=("email", "email address"),
                name_hints=("email", "candidate[email]"),
                required=True,
            ),
            BrowserFormField(
                key="location",
                value=profile.location,
                selectors=('#location', 'input[name="location"]'),
                label_hints=("location", "city"),
                name_hints=("location", "city"),
            ),
            BrowserFormField(
                key="headline",
                value=profile.headline,
                selectors=('#headline', 'textarea[name="headline"]'),
                label_hints=("headline", "summary", "current title"),
                name_hints=("headline", "summary", "current_title"),
            ),
            BrowserFormField(
                key="cover_note",
                value=packet.cover_note or "",
                selectors=('#cover_letter', 'textarea[name="cover_letter"]'),
                label_hints=("cover letter", "cover note", "why are you interested"),
                name_hints=("cover_letter", "coverLetter", "message"),
            ),
            BrowserFormField(
                key="tailored_resume_summary",
                value=packet.tailored_resume_summary or "",
                selectors=('#resume_summary', 'textarea[name="resume_summary"]'),
                label_hints=("resume summary", "professional summary"),
                name_hints=("resume_summary", "summary"),
            ),
        ]

        if resume_path is not None:
            fields.append(
                BrowserFormField(
                    key="resume_upload",
                    value=resume_path,
                    field_type="file",
                    selectors=(
                        'input[type="file"][name="resume"]',
                        'input[type="file"][name="resume_file"]',
                        'input[type="file"][accept*="pdf"]',
                    ),
                    label_hints=("resume", "upload resume"),
                    name_hints=("resume", "resume_file", "attachment"),
                    required=True,
                )
            )

        for answer_key, answer_value in packet.screening_answers.items():
            label_hints = SCREENING_LABEL_HINTS.get(answer_key, (answer_key.replace("_", " "),))
            fields.append(
                BrowserFormField(
                    key=answer_key,
                    value=str(answer_value),
                    selectors=(f'textarea[name="{answer_key}"]', f'input[name="{answer_key}"]'),
                    label_hints=tuple(label_hints),
                    name_hints=(answer_key, answer_key.replace("_", "-")),
                )
            )

        return [field for field in fields if str(field.value).strip()]

    def state_key(self, job: Job) -> str:
        hostname = urlparse(job.application_url or "").hostname or job.job_source.slug.value
        return f"{job.job_source.slug.value}-{hostname}"


GREENHOUSE_BROWSER_HOOK = BrowserSiteAdapterHook(
    name="Greenhouse Browser Assist",
    host_patterns=("greenhouse.io",),
    submit_selectors=(
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit Application")',
        'button:has-text("Apply")',
    ),
    confirmation_keywords=(
        "application submitted",
        "thank you for applying",
        "we have received your application",
    ),
    success_url_fragments=("thank_you", "confirmation"),
)

LEVER_BROWSER_HOOK = BrowserSiteAdapterHook(
    name="Lever Browser Assist",
    host_patterns=("lever.co",),
    submit_selectors=(
        'button[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
    ),
    confirmation_keywords=(
        "application submitted",
        "thanks for applying",
        "your application has been submitted",
    ),
    success_url_fragments=("thanks", "submitted"),
)

LINKEDIN_BROWSER_HOOK = BrowserSiteAdapterHook(
    name="LinkedIn Manual Only",
    host_patterns=("linkedin.com",),
    submit_selectors=(),
    confirmation_keywords=(),
    manual_only=True,
)

HANDSHAKE_BROWSER_HOOK = BrowserSiteAdapterHook(
    name="Handshake Manual Only",
    host_patterns=("joinhandshake.com",),
    submit_selectors=(),
    confirmation_keywords=(),
    manual_only=True,
)

GENERIC_BROWSER_HOOK = BrowserSiteAdapterHook(
    name="Generic Browser Assist",
    host_patterns=(),
    submit_selectors=(
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send Application")',
    ),
    confirmation_keywords=(
        "application submitted",
        "thank you for applying",
        "thanks for applying",
        "we have received your application",
    ),
    success_url_fragments=("submitted", "thank", "confirmation"),
)


def resolve_site_adapter_hook(job: Job) -> BrowserSiteAdapterHook:
    for hook in (
        LINKEDIN_BROWSER_HOOK,
        HANDSHAKE_BROWSER_HOOK,
        GREENHOUSE_BROWSER_HOOK,
        LEVER_BROWSER_HOOK,
    ):
        if hook.matches(job):
            return hook

    if job.job_source.slug == JobSource.GREENHOUSE:
        return GREENHOUSE_BROWSER_HOOK
    if job.job_source.slug == JobSource.LEVER:
        return LEVER_BROWSER_HOOK
    return GENERIC_BROWSER_HOOK


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.split() if part]
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if parts:
        return parts[0], parts[0]
    return "", ""
