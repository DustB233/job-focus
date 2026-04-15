from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Any, Protocol

from job_focus_shared import DiscoveredJobDTO, EmploymentType, JobSource, WorkMode

TAG_PATTERN = re.compile(r"<[^>]+>")
SALARY_RANGE_PATTERN = re.compile(
    r"\$?\s*(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?)\s*([kK])?\s*(?:-|to|–|—)\s*\$?\s*(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?)\s*([kK])?"
)


class SourceAdapter(Protocol):
    name: str
    slug: JobSource
    source_id: str | None
    source_display_name: str
    source_external_identifier: str | None
    base_url: str | None

    def fetch_jobs(self, *, run_at: datetime | None = None) -> list[DiscoveredJobDTO]:
        ...


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def title_case_slug(value: str) -> str:
    parts = re.split(r"[-_]+", value)
    return " ".join(part.title() for part in parts if part)


def normalize_text(value: Any, *, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        normalized = " ".join(value.split()).strip()
        return normalized or fallback
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        joined = ", ".join(normalize_text(item) for item in value if normalize_text(item))
        return joined or fallback
    if isinstance(value, dict):
        for key in ("name", "text", "value", "label"):
            if key in value:
                return normalize_text(value[key], fallback=fallback)
    return fallback


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    with_breaks = re.sub(r"(?i)<br\s*/?>", "\n", value)
    without_tags = TAG_PATTERN.sub(" ", with_breaks)
    return " ".join(unescape(without_tags).split()).strip()


def build_description(*candidates: Any) -> str:
    for candidate in candidates:
        if isinstance(candidate, str):
            cleaned = strip_html(candidate)
            if cleaned:
                return cleaned
        else:
            cleaned = normalize_text(candidate)
            if cleaned:
                return cleaned
    return "No description provided."


def parse_datetime_value(value: Any, *, fallback: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1_000_000_000_000 else value
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return fallback or utc_now()


def infer_work_mode(*, location: str, workplace_type: str | None = None, description: str = "") -> WorkMode:
    text = " ".join(filter(None, [location, workplace_type or "", description])).lower()
    if "hybrid" in text or "flexible" in text:
        return WorkMode.HYBRID
    if "remote" in text or "work from home" in text:
        return WorkMode.REMOTE
    return WorkMode.ONSITE


def infer_employment_type(*candidates: Any) -> EmploymentType:
    text = " ".join(_flatten_text(candidate) for candidate in candidates).lower()
    if "intern" in text:
        return EmploymentType.INTERNSHIP
    if "contract" in text or "consult" in text or "freelance" in text or "temporary" in text:
        return EmploymentType.CONTRACT
    return EmploymentType.FULL_TIME


def extract_salary_range(*candidates: Any) -> tuple[int, int]:
    for candidate in candidates:
        direct_range = _extract_direct_salary_range(candidate)
        if direct_range != (0, 0):
            return direct_range

    combined_text = " ".join(_flatten_text(candidate) for candidate in candidates)
    match = SALARY_RANGE_PATTERN.search(combined_text)
    if match is None:
        return 0, 0

    minimum = _parse_salary_number(match.group(1), match.group(2))
    maximum = _parse_salary_number(match.group(3), match.group(4))
    return (minimum, maximum) if minimum <= maximum else (maximum, minimum)


def infer_seniority(title: str, description: str) -> str | None:
    text = f"{title} {description}".lower()
    for keyword in ("principal", "director", "lead", "senior", "staff", "manager", "mid", "entry"):
        if keyword in text:
            return keyword
    if "intern" in text:
        return "intern"
    return None


def infer_authorization_requirement(description: str) -> str | None:
    text = description.lower()
    if (
        "no sponsorship" in text
        or "no visa sponsorship" in text
        or "unable to sponsor" in text
        or "cannot sponsor" in text
    ):
        return "No visa sponsorship available."
    if "work authorization" in text or "authorized to work" in text:
        return "Valid work authorization required."
    return None


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return strip_html(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    return ""


def _extract_direct_salary_range(candidate: Any) -> tuple[int, int]:
    if not isinstance(candidate, dict):
        return 0, 0

    key_groups = [
        ("min", "max"),
        ("minimum", "maximum"),
        ("salary_min", "salary_max"),
        ("min_salary", "max_salary"),
    ]
    for minimum_key, maximum_key in key_groups:
        minimum = candidate.get(minimum_key)
        maximum = candidate.get(maximum_key)
        if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)):
            min_value = int(minimum)
            max_value = int(maximum)
            return (min_value, max_value) if min_value <= max_value else (max_value, min_value)

    return 0, 0


def _parse_salary_number(value: str, thousands_suffix: str | None) -> int:
    normalized = value.replace(",", "")
    amount = float(normalized)
    if thousands_suffix:
        amount *= 1000
    elif amount < 1000:
        amount *= 1000
    return int(amount)
