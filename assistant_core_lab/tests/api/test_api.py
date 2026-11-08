from collections.abc import AsyncIterator, Callable

import httpx
import pytest
from fastapi import FastAPI

from assistant_api.main import create_app
from assistant_api.weather import WeatherClient

OK_JSON = {
    "current": {
        "time": "2026-10-05T09:00",
        "temperature_2m": 31.2,
        "weather_code": 3,
        "wind_speed_10m": 8.5,
    }
}


def weather_with(handler: Callable[[httpx.Request], httpx.Response]) -> WeatherClient:
    transport = httpx.MockTransport(handler)
    return WeatherClient("https://example.test/forecast", 10.76, 106.68, retries=1, transport=transport)


def api_client(app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(settings, service) -> AsyncIterator[httpx.AsyncClient]:
    settings = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 5})
    app = create_app(settings, service, weather_with(lambda _: httpx.Response(200, json=OK_JSON)))
    async with api_client(app) as async_client:
        yield async_client


@pytest.mark.anyio
async def test_health(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_chat_fee(client: httpx.AsyncClient) -> None:
    response = await client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "fee"
    assert "9,450,000" in body["answer"]
    assert body["request_id"]


@pytest.mark.anyio
async def test_chat_validation_error(client: httpx.AsyncClient) -> None:
    response = await client.post("/v1/chat", json={"message": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.anyio
async def test_rate_limit(client: httpx.AsyncClient) -> None:
    codes = [(await client.post("/v1/chat", json={"message": "hi"})).status_code for _ in range(6)]

    assert codes[-1] == 429


@pytest.mark.anyio
async def test_feedback_roundtrip(client: httpx.AsyncClient) -> None:
    chat = await client.post("/v1/chat", json={"message": "hi"})
    assert chat.status_code == 200
    request_id = chat.json()["request_id"]
    response = await client.post("/v1/feedback", json={"request_id": request_id, "rating": 1})

    assert response.status_code == 201
    assert response.json()["id"] == 1

    unauthorized = await client.get("/v1/feedback")
    assert unauthorized.status_code == 401

    listed = await client.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.anyio
async def test_feedback_rating_out_of_range(client: httpx.AsyncClient) -> None:
    response = await client.post("/v1/feedback", json={"request_id": "x", "rating": 5})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.anyio
async def test_weather_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/weather")

    assert response.status_code == 200
    assert response.json()["description"] == "overcast"


@pytest.mark.anyio
async def test_weather_down_returns_503(settings, service) -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    app = create_app(settings, service, weather_with(boom))
    async with api_client(app) as client:
        response = await client.get("/v1/weather")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "weather_service_unavailable"


@pytest.mark.anyio
async def test_weather_stale_cache_when_upstream_fails(settings, service) -> None:
    calls = {"n": 0}

    def flaky(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json=OK_JSON)
        return httpx.Response(500)

    weather = weather_with(flaky)
    weather.cache_ttl_s = 0  # force a refresh on the second call
    app = create_app(settings, service, weather)
    async with api_client(app) as client:
        first = await client.get("/v1/weather")
        second = await client.get("/v1/weather")

    assert first.status_code == second.status_code == 200
    assert first.json()["stale"] is False
    assert second.json()["stale"] is True
    assert second.json()["temperature_c"] == first.json()["temperature_c"]


@pytest.mark.anyio
async def test_offices_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/offices")

    assert response.status_code == 200
    offices = response.json()
    assert isinstance(offices, list)
    assert [office["name"] for office in offices] == sorted(office["name"] for office in offices)
    assert all(set(office) == {"name", "room", "hours"} for office in offices)


@pytest.mark.anyio
async def test_offices_contains_library(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/offices")

    assert {"name": "Library", "room": "B.201", "hours": "Mon-Sat 07:00-20:00"} in response.json()
