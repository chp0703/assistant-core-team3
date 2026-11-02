"""T5: unit and HTTP tests for per-client rate limiting, without sleeping."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api import main as api_main
from assistant_api.ratelimit import RateLimiter


@dataclass
class Clock:
    """A manually controlled monotonic clock for boundary tests."""

    now: float = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "2"])
def test_invalid_limit(limit) -> None:
    """Reject configurations that cannot define a positive request budget."""
    with pytest.raises(ValueError, match="positive integer"):
        RateLimiter(limit)


def test_exact_quota_and_independent_clients() -> None:
    """Accept exactly N hits per client, then reject without affecting others."""
    limiter = RateLimiter(2, clock=Clock())
    assert [limiter.allow("alice") for _ in range(3)] == [True, True, False]
    assert [limiter.allow("bob") for _ in range(3)] == [True, True, False]


def test_expiry_at_exactly_sixty_seconds() -> None:
    """The quota recovers at 60 seconds, not only after 60 seconds."""
    clock = Clock()
    limiter = RateLimiter(1, clock=clock)
    assert limiter.allow("alice")
    clock.now += 59.999
    assert not limiter.allow("alice")
    clock.now = 1060.0
    assert limiter.allow("alice")
    assert not limiter.allow("alice")


def test_sliding_window_and_rejections_do_not_extend_it() -> None:
    """Expire hits individually and never count rejected attempts."""
    clock = Clock()
    limiter = RateLimiter(2, clock=clock)
    assert limiter.allow("alice")
    clock.now += 30
    assert limiter.allow("alice")
    clock.now = 1059
    assert not limiter.allow("alice")
    clock.now = 1060
    assert limiter.allow("alice")
    assert not limiter.allow("alice")
    clock.now = 1090
    assert limiter.allow("alice")


def test_concurrent_requests_cannot_exceed_quota() -> None:
    """Count and record atomically when sync FastAPI handlers run in threads."""
    limiter = RateLimiter(5, clock=Clock())
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: limiter.allow("alice"), range(40)))
    assert sum(results) == 5


@pytest.fixture
def rate_app(settings, service, monkeypatch):
    """Build the actual application with a two-request quota and fake time."""
    clock = Clock()
    settings = settings.model_copy(update={"rate_limit_per_min": 2})
    # Only replace clock construction; exercise the real limiter and endpoint.
    monkeypatch.setattr(api_main, "RateLimiter", lambda limit: RateLimiter(limit, clock=clock))
    service.handle = Mock(wraps=service.handle)
    app = api_main.create_app(settings=settings, service=service)
    return app, clock, service


def test_http_429_shape_and_service_not_called_after_limit(rate_app) -> None:
    """Preserve the API error contract and stop before invoking the service."""
    app, _, service = rate_app
    with TestClient(app) as client:
        responses = [client.post("/v1/chat", json={"message": "hi"}) for _ in range(3)]
    assert [r.status_code for r in responses] == [200, 200, 429]
    assert responses[-1].json() == {
        "error": {"code": "rate_limit_exceeded", "message": "Rate limit exceeded"}
    }
    assert service.handle.call_count == 2


def test_http_resets_and_health_remains_available(rate_app) -> None:
    """Allow chat again at the expiry boundary while health stays unthrottled."""
    app, clock, _ = rate_app
    with TestClient(app) as client:
        for _ in range(2):
            assert client.post("/v1/chat", json={"message": "hi"}).status_code == 200
        assert client.post("/v1/chat", json={"message": "hi"}).status_code == 429
        assert client.get("/health").status_code == 200
        clock.now += 60
        assert client.post("/v1/chat", json={"message": "hi"}).status_code == 200


def test_invalid_body_does_not_consume_quota(rate_app) -> None:
    """Body validation occurs before the chat handler consumes quota."""
    app, _, _ = rate_app
    with TestClient(app) as client:
        assert client.post("/v1/chat", json={"message": ""}).status_code == 422
        assert client.post("/v1/chat", json={"message": "hi"}).status_code == 200
        assert client.post("/v1/chat", json={"message": "hi"}).status_code == 200
        assert client.post("/v1/chat", json={"message": "hi"}).status_code == 429


def test_session_and_forwarded_header_cannot_bypass_quota(rate_app) -> None:
    """Do not trust caller-controlled session IDs or forwarded IP headers."""
    app, _, _ = rate_app
    with TestClient(app) as client:
        responses = [
            client.post(
                "/v1/chat", json={"message": "hi", "session_id": str(index)},
                headers={"X-Forwarded-For": f"192.0.2.{index}"},
            )
            for index in range(3)
        ]
    assert [r.status_code for r in responses] == [200, 200, 429]


def test_http_distinct_peer_ips_have_distinct_budgets(rate_app) -> None:
    """Different ASGI peer addresses must not share the same counter."""
    app, _, _ = rate_app

    async def requests() -> list[int]:
        codes = []
        for ip in ("192.0.2.1", "192.0.2.2"):
            transport = httpx.ASGITransport(app=app, client=(ip, 12345))
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                for _ in range(3):
                    response = await client.post("/v1/chat", json={"message": "hi"})
                    codes.append(response.status_code)
        return codes

    assert asyncio.run(requests()) == [200, 200, 429, 200, 200, 429]


def test_app_instances_do_not_share_state(settings, service) -> None:
    """A new application instance has a fresh, independent limiter."""
    settings = settings.model_copy(update={"rate_limit_per_min": 1})
    apps = [api_main.create_app(settings=settings, service=service) for _ in range(2)]
    for app in apps:
        with TestClient(app) as client:
            assert client.post("/v1/chat", json={"message": "hi"}).status_code == 200
            assert client.post("/v1/chat", json={"message": "hi"}).status_code == 429
