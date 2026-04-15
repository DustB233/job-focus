from __future__ import annotations

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
    http_client: RateLimitedJsonClient | None = None,
) -> list[SourceAdapter]:
    client = http_client or RateLimitedJsonClient(
        timeout_seconds=settings.source_request_timeout_seconds,
        min_interval_seconds=settings.source_request_interval_seconds,
        max_retries=settings.source_max_retries,
        retry_backoff_seconds=settings.source_retry_backoff_seconds,
    )

    adapters: list[SourceAdapter] = []
    if settings.greenhouse_boards:
        adapters.append(GreenhouseJobAdapter(settings.greenhouse_boards, client))
    if settings.lever_sites:
        adapters.append(LeverJobAdapter(settings.lever_sites, client))

    adapters.append(LinkedInManualLinkAdapter())
    adapters.append(HandshakeManualLinkAdapter())
    return adapters


__all__ = [
    "GreenhouseJobAdapter",
    "HandshakeManualLinkAdapter",
    "LinkedInManualLinkAdapter",
    "ManualLinkPlaceholderAdapter",
    "build_source_adapters",
]
