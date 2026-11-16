"""T1 chat contract tests, independent of feedback, weather and the bonus task."""

import re
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_core.models import Intent, Message, Response, Source


@pytest.fixture
def chat_client(settings, service):
    with TestClient(create_app(settings=settings, service=service)) as client:
        yield client


@pytest.mark.parametrize(
    ("payload", "expected_session"),
    [
        ({"message": "hi"}, "anonymous"),
        ({"message": "hi", "session_id": "student-session"}, "student-session"),
        ({"message": "a" * 2000, "session_id": "s" * 64}, "s" * 64),
    ],
    ids=["default-session", "explicit-session", "maximum-lengths"],
)
def test_chat_forwards_message_and_session(chat_client, service, monkeypatch, payload, expected_session):
    handle = Mock(wraps=service.handle)
    monkeypatch.setattr(service, "handle", handle)

    response = chat_client.post("/v1/chat", json=payload)

    assert response.status_code == 200
    handle.assert_called_once_with(Message(text=payload["message"], session_id=expected_session))


def test_chat_preserves_service_response(chat_client, service, monkeypatch):
    result = Response(
        answer="A cached answer with its source.",
        intent=Intent.RULE,
        sources=[Source(id="rule-1", title="Registration")],
        degraded=True,
    )
    monkeypatch.setattr(service, "handle", Mock(return_value=result))

    response = chat_client.post("/v1/chat", json={"message": "registration rules"})

    assert response.status_code == 200
    body = response.json()
    request_id = body.pop("request_id")
    assert re.fullmatch(r"[0-9a-f]{12}", request_id)
    assert body == result.model_dump(mode="json")


def test_chat_generates_a_new_request_id_each_time(chat_client):
    responses = [chat_client.post("/v1/chat", json={"message": "hi"}) for _ in range(2)]

    assert all(response.status_code == 200 for response in responses)
    request_ids = [response.json()["request_id"] for response in responses]
    assert all(re.fullmatch(r"[0-9a-f]{12}", request_id) for request_id in request_ids)
    assert request_ids[0] != request_ids[1]


def test_chat_office_answer(chat_client):
    response = chat_client.post("/v1/chat", json={"message": "where is the library"})

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "office"
    assert "Library" in body["answer"] and "B.201" in body["answer"]
    assert body["sources"] == []
    assert body["degraded"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": "a" * 2001},
        {"message": 123},
        {"message": None},
        {"message": "hi", "session_id": "s" * 65},
        {"message": "hi", "session_id": None},
    ],
    ids=[
        "missing-message",
        "empty-message",
        "whitespace-message",
        "long-message",
        "wrong-type",
        "null-message",
        "long-session",
        "null-session",
    ],
)
def test_chat_invalid_input_returns_contract_error(chat_client, service, monkeypatch, payload):
    handle = Mock(wraps=service.handle)
    monkeypatch.setattr(service, "handle", handle)

    response = chat_client.post("/v1/chat", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert error["message"]
    handle.assert_not_called()


def test_chat_rag_enabled_preserves_schema_privacy_and_deterministic_routes(settings) -> None:
    rag_settings = settings.model_copy(update={"rag_enabled": True, "kb_dir": settings.data_dir / "kb"})
    with TestClient(create_app(settings=rag_settings)) as client:
        kb_res = client.post("/v1/chat", json={"message": "I lost my student card"})
        assert kb_res.status_code == 200
        kb_body = kb_res.json()
        assert set(kb_body) == {"answer", "intent", "sources", "degraded", "request_id"}
        assert kb_body["intent"] == "rule"
        assert [source["id"] for source in kb_body["sources"]] == ["S26#3"]

        privacy_res = client.post("/v1/chat", json={"message": "what grade did my friend get"})
        assert privacy_res.status_code == 200
        assert privacy_res.json()["intent"] == "unknown"
        assert privacy_res.json()["sources"] == []

        fee_res = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
        assert fee_res.status_code == 200
        assert fee_res.json()["intent"] == "fee" and "9,450,000 VND" in fee_res.json()["answer"]
