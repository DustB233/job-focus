from __future__ import annotations

from datetime import datetime, timezone

import pytest
from job_focus_shared import EmploymentType, JobSource, WorkMode

from worker.adapters.greenhouse import GreenhouseJobAdapter
from worker.adapters.lever import LeverJobAdapter
from worker.adapters.manual_links import HandshakeManualLinkAdapter, LinkedInManualLinkAdapter
from worker.clients.http import JsonResponse, RateLimitedJsonClient


class StubJsonClient:
    def __init__(self, payloads_by_url: dict[str, object]) -> None:
        self.payloads_by_url = payloads_by_url

    def get_json(self, url: str) -> object:
        return self.payloads_by_url[url]


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def test_greenhouse_adapter_normalizes_mocked_payload() -> None:
    client = StubJsonClient(
        {
            "https://boards-api.greenhouse.io/v1/boards/northstar": {
                "name": "Northstar Labs",
            },
            "https://boards-api.greenhouse.io/v1/boards/northstar/jobs?content=true": {
                "jobs": [
                    {
                        "id": 12345,
                        "title": "AI Program Manager",
                        "location": {"name": "Remote - US"},
                        "content": "<p>Compensation: $150,000 - $180,000</p><p>US work authorization required.</p>",
                        "absolute_url": "https://boards.greenhouse.io/northstar/jobs/12345",
                        "updated_at": "2026-04-12T17:00:00Z",
                        "metadata": [
                            {"name": "Employment Type", "value": "Full-time"},
                            {"name": "Workplace Type", "value": "Remote"},
                            {"name": "Seniority", "value": "Senior"},
                        ],
                    }
                ]
            },
        }
    )

    adapter = GreenhouseJobAdapter(["northstar"], client)  # type: ignore[arg-type]
    jobs = adapter.fetch_jobs(run_at=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc))

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == JobSource.GREENHOUSE
    assert job.external_job_id == "northstar:12345"
    assert job.company == "Northstar Labs"
    assert job.work_mode == WorkMode.REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME
    assert job.salary_min == 150000
    assert job.salary_max == 180000
    assert job.authorization_requirement == "Valid work authorization required."
    assert job.raw_payload["boardToken"] == "northstar"


def test_lever_adapter_normalizes_mocked_payload() -> None:
    client = StubJsonClient(
        {
            "https://api.lever.co/v0/postings/relay?mode=json": [
                {
                    "id": "abc123",
                    "text": "Operations Systems Lead",
                    "applyUrl": "https://jobs.lever.co/relay/abc123/apply",
                    "hostedUrl": "https://jobs.lever.co/relay/abc123",
                    "createdAt": 1_776_000_000_000,
                    "descriptionPlain": "No visa sponsorship. Lead AI platform operations and analytics.",
                    "workplaceType": "Hybrid",
                    "salaryRange": {"min": 160000, "max": 190000},
                    "categories": {
                        "location": "San Francisco, CA",
                        "commitment": "Full-time",
                    },
                }
            ]
        }
    )

    adapter = LeverJobAdapter(["relay"], client)  # type: ignore[arg-type]
    jobs = adapter.fetch_jobs(run_at=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc))

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == JobSource.LEVER
    assert job.external_job_id == "relay:abc123"
    assert job.company == "Relay"
    assert job.work_mode == WorkMode.HYBRID
    assert job.salary_min == 160000
    assert job.salary_max == 190000
    assert job.authorization_requirement == "No visa sponsorship available."
    assert job.raw_payload["siteName"] == "relay"


def test_manual_link_placeholders_do_not_scrape_and_support_manual_normalization() -> None:
    linkedin = LinkedInManualLinkAdapter()
    handshake = HandshakeManualLinkAdapter()

    assert linkedin.fetch_jobs() == []
    assert handshake.fetch_jobs() == []

    manual_job = linkedin.normalize_link(
        "https://www.linkedin.com/jobs/view/1234567890",
        company="Acme AI",
        title="Manual AI Program Manager",
    )
    assert manual_job.source == JobSource.MANUAL
    assert manual_job.application_url == "https://www.linkedin.com/jobs/view/1234567890"
    assert "Automated scraping and submission are disabled." in manual_job.description

    with pytest.raises(ValueError):
        handshake.normalize_link(
            "https://www.linkedin.com/jobs/view/1234567890",
            company="Acme AI",
            title="Wrong host",
        )


def test_rate_limited_client_retries_retryable_responses() -> None:
    responses = iter(
        [
            JsonResponse(status_code=429, payload={"detail": "Too many requests"}),
            JsonResponse(status_code=200, payload={"jobs": []}),
        ]
    )
    sleeps: list[float] = []

    client = RateLimitedJsonClient(
        min_interval_seconds=0,
        max_retries=2,
        retry_backoff_seconds=1.0,
        transport=lambda url: next(responses),
        sleep=sleeps.append,
    )

    payload = client.get_json("https://example.com/jobs")

    assert payload == {"jobs": []}
    assert sleeps == [1.0]


def test_rate_limited_client_waits_between_requests() -> None:
    clock = FakeClock()
    responses = iter(
        [
            JsonResponse(status_code=200, payload={"page": 1}),
            JsonResponse(status_code=200, payload={"page": 2}),
        ]
    )
    client = RateLimitedJsonClient(
        min_interval_seconds=2.0,
        max_retries=1,
        transport=lambda url: next(responses),
        sleep=clock.sleep,
        clock=clock.now,
    )

    first_payload = client.get_json("https://example.com/page-1")
    second_payload = client.get_json("https://example.com/page-2")

    assert first_payload == {"page": 1}
    assert second_payload == {"page": 2}
    assert clock.sleeps == [2.0]
