from __future__ import annotations

from collections.abc import Sequence

from app.models import JobSourceConfig
from job_focus_shared import JobSource

from worker.adapters.base import SourceAdapter
from worker.adapters.greenhouse import GreenhouseJobAdapter
from worker.adapters.lever import LeverJobAdapter
from worker.adapters.manual_links import (
    HandshakeManualLinkAdapter,
    LinkedInManualLinkAdapter,
    ManualLinkPlaceholderAdapter,
)
from worker.clients.http import RateLimitedJsonClient
from worker.config import WorkerSettings


def build_source_adapters(
    settings: WorkerSettings,
    sources: Sequence[JobSourceConfig] | None = None,
    http_client: RateLimitedJsonClient | None = None,
) -> list[SourceAdapter]:
    client = http_client or RateLimitedJsonClient(
        timeout_seconds=settings.source_request_timeout_seconds,
        min_interval_seconds=settings.source_request_interval_seconds,
        max_retries=settings.source_max_retries,
        retry_backoff_seconds=settings.source_retry_backoff_seconds,
    )

    adapters: list[SourceAdapter] = []
    if sources is not None:
        configured_sources = list(sources)
        for source in configured_sources:
            if not source.is_active or not source.external_identifier:
                continue
            if source.slug == JobSource.GREENHOUSE:
                adapters.append(
                    GreenhouseJobAdapter(
                        source.external_identifier,
                        client,
                        source_id=source.id,
                        source_display_name=source.display_name,
                    )
                )
            elif source.slug == JobSource.LEVER:
                adapters.append(
                    LeverJobAdapter(
                        source.external_identifier,
                        client,
                        source_id=source.id,
                        source_display_name=source.display_name,
                    )
                )
        return adapters

    for board_token in settings.greenhouse_boards:
        adapters.append(GreenhouseJobAdapter(board_token, client))
    for site_name in settings.lever_sites:
        adapters.append(LeverJobAdapter(site_name, client))
    return adapters


__all__ = [
    "GreenhouseJobAdapter",
    "HandshakeManualLinkAdapter",
    "LinkedInManualLinkAdapter",
    "ManualLinkPlaceholderAdapter",
    "build_source_adapters",
]
