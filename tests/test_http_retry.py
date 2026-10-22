"""Bounded upstream retry policy tests."""

import httpx
import pytest

from fieldsat.providers.http_retry import request_with_retry


@pytest.mark.asyncio
async def test_retries_rate_limit_and_honors_retry_after() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "0.75"}),
        httpx.Response(200),
    ]
    delays: list[float] = []

    async def operation() -> httpx.Response:
        return responses.pop(0)

    async def sleep(delay: float) -> None:
        delays.append(delay)

    response = await request_with_retry(
        operation,
        provider="test",
        correlation_id="correlation",
        sleep=sleep,
        jitter=lambda: 0,
    )

    assert response.status_code == 200
    assert delays == [0.75]


@pytest.mark.asyncio
async def test_retries_server_and_transport_failures_with_a_bound() -> None:
    outcomes: list[httpx.Response | Exception] = [
        httpx.ReadTimeout("timeout"),
        httpx.Response(503),
        httpx.Response(200),
    ]
    delays: list[float] = []

    async def operation() -> httpx.Response:
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def sleep(delay: float) -> None:
        delays.append(delay)

    response = await request_with_retry(
        operation,
        provider="test",
        correlation_id="correlation",
        sleep=sleep,
        jitter=lambda: 0,
    )

    assert response.status_code == 200
    assert delays == [0.2, 0.4]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 403])
async def test_does_not_retry_non_retryable_client_errors(status: int) -> None:
    calls = 0

    async def operation() -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status)

    response = await request_with_retry(
        operation,
        provider="test",
        correlation_id="correlation",
    )

    assert response.status_code == status
    assert calls == 1
