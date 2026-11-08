"""R1 feedback creation checks, independent of the R2 listing task."""

from datetime import datetime

import httpx
import pytest
from sqlmodel import Session, select

from assistant_api.db import Feedback, Repository, init_db, make_engine
from assistant_api.main import create_app


@pytest.fixture
def repo():
    engine = make_engine("sqlite://")
    init_db(engine)
    yield Repository(engine, "test-salt")
    engine.dispose()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client(settings, service, repo):
    app = create_app(settings=settings, service=service, repo=repo)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.parametrize("rating,comment", [(-1, "Cần sửa câu trả lời"), (0, None), (1, "x" * 500)])
@pytest.mark.anyio
async def test_post_feedback_saves_fields(client, repo, rating, comment):
    chat = await client.post("/v1/chat", json={"message": "hi"})
    assert chat.status_code == 200
    request_id = chat.json()["request_id"]
    payload = {"request_id": request_id, "rating": rating}
    if comment is not None:
        payload["comment"] = comment

    response = await client.post("/v1/feedback", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["request_id"] == request_id
    assert body["rating"] == rating
    assert body["comment"] == comment
    with Session(repo.engine) as db:
        saved = db.exec(select(Feedback)).one()
        assert (saved.id, saved.request_id, saved.rating, saved.comment) == (1, request_id, rating, comment)
        assert saved.created_at == datetime.fromisoformat(body["created_at"])


@pytest.mark.anyio
async def test_unknown_request_returns_404_without_saving(client, repo):
    response = await client.post("/v1/feedback", json={"request_id": "missing", "rating": 1})

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "unknown_request_id", "message": "Unknown request id"}}
    with Session(repo.engine) as db:
        assert db.exec(select(Feedback)).all() == []


@pytest.mark.parametrize("rating,comment", [(-2, None), (2, None), (1, "x" * 501)])
@pytest.mark.anyio
async def test_invalid_feedback_returns_422_without_saving(client, repo, rating, comment):
    repo.record_interaction("s", "r1", "greeting", None, True, False, 1.0)
    response = await client.post("/v1/feedback", json={"request_id": "r1", "rating": rating, "comment": comment})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    with Session(repo.engine) as db:
        assert db.exec(select(Feedback)).all() == []


def test_feedback_survives_reopening_database(tmp_path):
    url = f"sqlite:///{(tmp_path / 'feedback.db').as_posix()}"
    engine = make_engine(url)
    try:
        init_db(engine)
        repo = Repository(engine, "test-salt")
        repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
        saved = repo.add_feedback("r1", -1, "wrong fee")
        assert saved is not None
        feedback_id, created_at = saved.id, saved.created_at
    finally:
        engine.dispose()

    reopened = make_engine(url)
    try:
        with Session(reopened) as db:
            feedback = db.get(Feedback, feedback_id)
            assert feedback is not None
            assert (feedback.request_id, feedback.rating, feedback.comment) == ("r1", -1, "wrong fee")
            assert feedback.created_at == created_at
    finally:
        reopened.dispose()
