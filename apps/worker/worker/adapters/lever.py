from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import quote

from job_focus_shared import DiscoveredJobDTO, JobSource

from worker.adapters.base import (
    SourceAdapter,
    build_description,
    extract_salary_range,
    infer_authorization_requirement,
    infer_employment_type,
    infer_seniority,
    infer_work_mode,
    normalize_text,
    parse_datetime_value,
    title_case_slug,
)
from worker.clients.http import RateLimitedJsonClient


class LeverJobAdapter(SourceAdapter):
    name = "Lever"
    slug = JobSource.LEVER
    source_id: str | None

    def __init__(
        self,
        site_name: str,
        http_client: RateLimitedJsonClient,
        *,
        source_id: str | None = None,
        source_display_name: str | None = None,
    ) -> None:
        normalized_site_name = site_name.strip()
        self.source_id = source_id
        self.site_name = normalized_site_name
        self.source_external_identifier = normalized_site_name
        self.source_display_name = source_display_name or f"Lever / {title_case_slug(normalized_site_name)}"
        self.base_url = f"https://api.lever.co/v0/postings/{quote(normalized_site_name, safe='')}?mode=json"
        self.http_client = http_client

    def fetch_jobs(self, *, run_at: datetime | None = None) -> list[DiscoveredJobDTO]:
        payload = self.http_client.get_json(self.base_url)
        raw_jobs = payload if isinstance(payload, list) else payload.get("data", [])
        company_name = title_case_slug(self.site_name)
        return [
            self._normalize_job(
                site_name=self.site_name,
                company_name=company_name,
                raw_job=raw_job,
                run_at=run_at,
            )
            for raw_job in raw_jobs
        ]

    def _normalize_job(
        self,
        *,
        site_name: str,
        company_name: str,
        raw_job: dict[str, Any],
        run_at: datetime | None,
    ) -> DiscoveredJobDTO:
        categories = raw_job.get("categories") if isinstance(raw_job.get("categories"), dict) else {}
        location = normalize_text(
            categories.get("location") or categories.get("allLocations"),
            fallback="Unspecified",
        )
        description = build_description(raw_job.get("descriptionPlain"), raw_job.get("description"))
        salary_min, salary_max = extract_salary_range(raw_job.get("salaryRange"), description)
        workplace_type = normalize_text(raw_job.get("workplaceType"))
        commitment = normalize_text(categories.get("commitment"))

        return DiscoveredJobDTO(
            source=self.slug,
            external_job_id=f"{site_name}:{raw_job.get('id')}",
            company=normalize_text(raw_job.get("company"), fallback=company_name),
            title=normalize_text(raw_job.get("text"), fallback="Untitled role"),
            location=location,
            work_mode=infer_work_mode(
                location=location,
                workplace_type=workplace_type,
                description=description,
            ),
            employment_type=infer_employment_type(commitment, description),
            salary_min=salary_min,
            salary_max=salary_max,
            description=description,
            application_url=normalize_text(raw_job.get("applyUrl") or raw_job.get("hostedUrl")) or None,
            seniority_level=infer_seniority(
                normalize_text(raw_job.get("text"), fallback="Untitled role"),
                description,
            ),
            authorization_requirement=infer_authorization_requirement(description),
            posted_at=parse_datetime_value(raw_job.get("createdAt"), fallback=run_at),
            raw_payload={
                "siteName": site_name,
                "job": raw_job,
            },
        )
