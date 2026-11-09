"""Lab 5 Part E.6 integration checks: API + SQLite across a server restart, and what the database holds."""

import sqlite3

import httpx
import pytest

from assistant_api.main import create_app

ADMIN = {"X-API-Key": "secret-admin"}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def file_settings(settings, tmp_path):
    url = f"sqlite:///{(tmp_path / 'assistant.db').as_posix()}"
    return settings.model_copy(update={"api_admin_key": "secret-admin", "database_url": url})


def api_client(app) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.anyio
async def test_feedback_flow_survives_a_restart(file_settings, service) -> None:
    async with api_client(create_app(file_settings, service)) as first:
        chat = await first.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
        request_id = chat.json()["request_id"]
        saved = await first.post("/v1/feedback", json={"request_id": request_id, "rating": 1, "comment": "clear"})
        unknown = await first.post("/v1/feedback", json={"request_id": "nope", "rating": 1})

    assert (chat.status_code, saved.status_code, unknown.status_code) == (200, 201, 404)

    async with api_client(create_app(file_settings, service)) as restarted:
        no_key = await restarted.get("/v1/feedback")
        listed = await restarted.get("/v1/feedback", headers=ADMIN)
        second = await restarted.post("/v1/feedback", json={"request_id": request_id, "rating": -1})
        relisted = await restarted.get("/v1/feedback", headers=ADMIN)

    assert no_key.status_code == 401
    assert listed.json() == [saved.json()]
    assert second.json()["id"] == saved.json()["id"] + 1
    assert [row["rating"] for row in relisted.json()] == [-1, 1]


@pytest.mark.anyio
async def test_database_keeps_three_tables_and_no_raw_text(file_settings, service) -> None:
    message, session = "my phone is 0901234567, tuition for 18 credits", "student-nguyen-van-a"
    async with api_client(create_app(file_settings, service)) as client:
        chat = await client.post("/v1/chat", json={"message": message, "session_id": session})
        await client.post("/v1/feedback", json={"request_id": chat.json()["request_id"], "rating": 0})

    con = sqlite3.connect(file_settings.database_url.removeprefix("sqlite:///"))
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        cells = [
            str(cell)
            for table in ("chat_session", "interaction", "feedback")
            for row in con.execute(f"SELECT * FROM {table}")  # noqa: S608 - fixed table names
            for cell in row
        ]
        counts = [
            con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("chat_session", "interaction", "feedback")
        ]
    finally:
        con.close()

    assert {"chat_session", "interaction", "feedback"} <= tables
    assert counts == [1, 1, 1]
    assert not any(secret in cell for cell in cells for secret in (session, "0901234567", "tuition"))
