from __future__ import annotations

from collections.abc import Sequence
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


class GreenhouseJobAdapter(SourceAdapter):
    name = "Greenhouse"
    slug = JobSource.GREENHOUSE
    source_display_name = "Greenhouse"
    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, board_tokens: Sequence[str], http_client: RateLimitedJsonClient) -> None:
        self.board_tokens = [token.strip() for token in board_tokens if token.strip()]
        self.http_client = http_client

    def fetch_jobs(self, *, run_at: datetime | None = None) -> list[DiscoveredJobDTO]:
        discovered_jobs: list[DiscoveredJobDTO] = []
        for board_token in self.board_tokens:
            board_url = f"{self.base_url}/{quote(board_token, safe='')}"
            jobs_url = f"{board_url}/jobs?content=true"

            board_payload = self.http_client.get_json(board_url)
            jobs_payload = self.http_client.get_json(jobs_url)
            company_name = normalize_text(
                board_payload.get("name") if isinstance(board_payload, dict) else None,
                fallback=title_case_slug(board_token),
            )

            raw_jobs = jobs_payload.get("jobs", []) if isinstance(jobs_payload, dict) else []
            for raw_job in raw_jobs:
                discovered_jobs.append(
                    self._normalize_job(
                        board_token=board_token,
                        company_name=company_name,
                        raw_job=raw_job,
                        run_at=run_at,
                    )
                )
        return discovered_jobs

    def _normalize_job(
        self,
        *,
        board_token: str,
        company_name: str,
        raw_job: dict[str, Any],
        run_at: datetime | None,
    ) -> DiscoveredJobDTO:
        metadata = _metadata_to_dict(raw_job.get("metadata"))
        location = normalize_text(raw_job.get("location"), fallback="Unspecified")
        description = build_description(raw_job.get("content"), raw_job.get("description"))
        salary_min, salary_max = extract_salary_range(
            raw_job.get("pay_input_ranges"),
            metadata,
            description,
        )

        external_id = f"{board_token}:{raw_job.get('id') or raw_job.get('internal_job_id')}"
        workplace_type = metadata.get("workplace type")
        seniority_level = metadata.get("seniority") or metadata.get("level") or infer_seniority(
            normalize_text(raw_job.get("title"), fallback="Untitled role"),
            description,
        )

        return DiscoveredJobDTO(
            source=self.slug,
            external_job_id=external_id,
            company=normalize_text(raw_job.get("company"), fallback=company_name),
            title=normalize_text(raw_job.get("title"), fallback="Untitled role"),
            location=location,
            work_mode=infer_work_mode(
                location=location,
                workplace_type=workplace_type,
                description=description,
            ),
            employment_type=infer_employment_type(
                metadata.get("employment type"),
                metadata.get("commitment"),
                description,
            ),
            salary_min=salary_min,
            salary_max=salary_max,
            description=description,
            application_url=normalize_text(raw_job.get("absolute_url")) or None,
            seniority_level=seniority_level,
            authorization_requirement=(
                metadata.get("work authorization")
                or infer_authorization_requirement(description)
            ),
            posted_at=parse_datetime_value(
                raw_job.get("updated_at") or raw_job.get("created_at"),
                fallback=run_at,
            ),
            raw_payload={
                "boardToken": board_token,
                "job": raw_job,
            },
        )


def _metadata_to_dict(metadata: Any) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not isinstance(metadata, list):
        return normalized

    for entry in metadata:
        if not isinstance(entry, dict):
            continue
        key = normalize_text(
            entry.get("name") or entry.get("label") or entry.get("key")
        ).lower()
        value = normalize_text(entry.get("value") or entry.get("text") or entry.get("label"))
        if key and value:
            normalized[key] = value
    return normalized
