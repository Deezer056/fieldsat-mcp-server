"""Small bounded retry and redacted structured logging helpers for provider HTTP."""

import asyncio
import json
import logging
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

LOGGER = logging.getLogger("fieldsat.providers")

type ResponseOperation = Callable[[], Awaitable[httpx.Response]]
type Sleep = Callable[[float], Awaitable[None]]
type Jitter = Callable[[], float]


def log_provider_event(event: str, **details: object) -> None:
    payload = {"event": event, **details}
    LOGGER.info(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def _retry_after_seconds(response: httpx.Response, maximum: float) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return min(maximum, max(0.0, float(raw)))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return min(maximum, max(0.0, (retry_at - datetime.now(UTC)).total_seconds()))


async def request_with_retry(
    operation: ResponseOperation,
    *,
    provider: str,
    correlation_id: str,
    sleep: Sleep = asyncio.sleep,
    jitter: Jitter = random.random,
    maximum_attempts: int = 3,
    base_delay_seconds: float = 0.2,
    maximum_delay_seconds: float = 2.0,
) -> httpx.Response:
    """Retry rate limits, 5xx, timeouts, and network errors within a short budget."""
    if maximum_attempts < 1:
        raise ValueError("maximum_attempts must be positive.")

    for attempt in range(1, maximum_attempts + 1):
        try:
            response = await operation()
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == maximum_attempts:
                raise
            delay = min(maximum_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))
            delay += min(base_delay_seconds, max(0.0, jitter()) * base_delay_seconds)
            log_provider_event(
                "upstream_retry",
                provider=provider,
                correlation_id=correlation_id,
                attempt=attempt,
                reason="transport_error",
                delay_ms=round(delay * 1000),
            )
            await sleep(delay)
            continue

        retryable_status = response.status_code == 429 or response.status_code >= 500
        if not retryable_status or attempt == maximum_attempts:
            return response

        retry_after = _retry_after_seconds(response, maximum_delay_seconds)
        delay = retry_after
        if delay is None:
            delay = min(maximum_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))
            delay += min(base_delay_seconds, max(0.0, jitter()) * base_delay_seconds)
        log_provider_event(
            "upstream_retry",
            provider=provider,
            correlation_id=correlation_id,
            attempt=attempt,
            status_class=f"{response.status_code // 100}xx",
            delay_ms=round(delay * 1000),
        )
        await sleep(delay)

    raise AssertionError("The bounded retry loop must return or raise.")
