from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True, slots=True)
class JsonResponse:
    status_code: int
    payload: Any


class HttpTransportError(RuntimeError):
    pass


class HttpRequestError(RuntimeError):
    def __init__(self, url: str, status_code: int | None, payload: Any) -> None:
        self.url = url
        self.status_code = status_code
        self.payload = payload
        status_text = str(status_code) if status_code is not None else "transport_error"
        super().__init__(f"HTTP request failed for {url} with status {status_text}.")


def _decode_payload(body: bytes) -> Any:
    if not body:
        return {}

    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def build_urlopen_transport(timeout_seconds: float) -> Callable[[str], JsonResponse]:
    def transport(url: str) -> JsonResponse:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "JobFocusWorker/0.1",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return JsonResponse(
                    status_code=getattr(response, "status", 200),
                    payload=_decode_payload(response.read()),
                )
        except HTTPError as error:
            return JsonResponse(status_code=error.code, payload=_decode_payload(error.read()))
        except URLError as error:
            raise HttpTransportError(str(error.reason)) from error

    return transport


class RateLimitedJsonClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        min_interval_seconds: float = 0.5,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        transport: Callable[[str], JsonResponse] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.min_interval_seconds = max(min_interval_seconds, 0.0)
        self.max_retries = max(max_retries, 1)
        self.retry_backoff_seconds = max(retry_backoff_seconds, 0.0)
        self._transport = transport or build_urlopen_transport(timeout_seconds)
        self._sleep = sleep
        self._clock = clock
        self._next_request_at = 0.0

    def get_json(self, url: str) -> Any:
        last_transport_error: HttpTransportError | None = None

        for attempt in range(1, self.max_retries + 1):
            self._wait_for_slot()
            try:
                response = self._transport(url)
            except HttpTransportError as error:
                last_transport_error = error
                if attempt == self.max_retries:
                    raise HttpRequestError(url, None, {"detail": str(error)}) from error
                self._sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code < 400:
                return response.payload

            if response.status_code not in RETRYABLE_STATUS_CODES or attempt == self.max_retries:
                raise HttpRequestError(url, response.status_code, response.payload)

            self._sleep(self.retry_backoff_seconds * attempt)

        raise HttpRequestError(
            url,
            None,
            {"detail": str(last_transport_error) if last_transport_error is not None else "Unknown error"},
        )

    def _wait_for_slot(self) -> None:
        if self.min_interval_seconds == 0:
            return

        now = self._clock()
        if now < self._next_request_at:
            self._sleep(self._next_request_at - now)
            now = self._clock()
        self._next_request_at = now + self.min_interval_seconds
