from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from hashlib import sha1
from urllib.parse import urlparse

from job_focus_shared import DiscoveredJobDTO, EmploymentType, JobSource, WorkMode

from worker.adapters.base import SourceAdapter, normalize_text


class ManualLinkPlaceholderAdapter(SourceAdapter):
    slug = JobSource.MANUAL
    source_display_name = "Manual Link"
    base_url = None

    def __init__(self, *, name: str, supported_hosts: Sequence[str]) -> None:
        self.name = name
        self.supported_hosts = tuple(host.lower() for host in supported_hosts)

    def fetch_jobs(self, *, run_at: datetime | None = None) -> list[DiscoveredJobDTO]:
        return []

    def normalize_link(
        self,
        url: str,
        *,
        company: str,
        title: str,
        location: str = "Manual review required",
        posted_at: datetime | None = None,
    ) -> DiscoveredJobDTO:
        hostname = urlparse(url).netloc.lower()
        if not any(hostname.endswith(host) for host in self.supported_hosts):
            raise ValueError(f"{self.name} adapter does not accept host '{hostname}'.")

        external_id = sha1(url.encode("utf-8")).hexdigest()
        return DiscoveredJobDTO(
            source=self.slug,
            external_job_id=f"{self.name.lower().replace(' ', '-')}:manual:{external_id}",
            company=normalize_text(company, fallback=self.name),
            title=normalize_text(title, fallback="Manual link"),
            location=normalize_text(location, fallback="Manual review required"),
            work_mode=WorkMode.ONSITE,
            employment_type=EmploymentType.FULL_TIME,
            salary_min=0,
            salary_max=0,
            description=f"Manual {self.name} link placeholder. Automated scraping and submission are disabled.",
            application_url=url,
            seniority_level=None,
            authorization_requirement=None,
            posted_at=posted_at or datetime.now(timezone.utc),
            raw_payload={
                "provider": self.name,
                "url": url,
            },
        )


class LinkedInManualLinkAdapter(ManualLinkPlaceholderAdapter):
    def __init__(self) -> None:
        super().__init__(
            name="LinkedIn Manual Link",
            supported_hosts=("linkedin.com",),
        )


class HandshakeManualLinkAdapter(ManualLinkPlaceholderAdapter):
    def __init__(self) -> None:
        super().__init__(
            name="Handshake Manual Link",
            supported_hosts=("joinhandshake.com", "app.joinhandshake.com"),
        )
