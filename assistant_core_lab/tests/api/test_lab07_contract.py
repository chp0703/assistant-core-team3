"""Lab 07 Foundation: HTTP API contract tests for escalation, privacy, feedback, and errors."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_core.guard import PRIVATE_REPLY
from assistant_core.llm import StubLLM
from assistant_core.service import create_service
from ui.api_client import AssistantClient


@pytest.fixture
def rag_app(settings):
    rag_settings = settings.model_copy(
        update={
            "rag_enabled": True,
            "kb_dir": settings.data_dir / "kb",
            "rate_limit_per_min": 5,
            "api_admin_key": "test-admin",
        }
    )
    return create_app(settings=rag_settings)


def test_health_endpoint_contract(rag_app) -> None:
    with TestClient(rag_app) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok" and res.json()["version"]


def test_chat_source_escalation_privacy_and_deterministic_contract(rag_app) -> None:
    with TestClient(rag_app) as client:
        # Grounded KB rule answer -> sources populated, escalate=False
        rule_res = client.post("/v1/chat", json={"message": "can I register my thesis with 118 credits"})
        assert rule_res.status_code == 200
        rule_body = rule_res.json()
        assert rule_body["intent"] == "rule"
        assert [s["id"] for s in rule_body["sources"]] == ["H26#5.3"]
        assert rule_body["escalate"] is False
        assert rule_body["degraded"] is False
        assert rule_body["request_id"]

        # Out-of-scope / no evidence -> escalate=True
        oos_res = client.post("/v1/chat", json={"message": "what is the capital of France"})
        assert oos_res.status_code == 200
        oos_body = oos_res.json()
        assert oos_body["intent"] == "unknown"
        assert oos_body["sources"] == []
        assert oos_body["escalate"] is True
        assert oos_body["degraded"] is False

        # Privacy refusal -> intent=unknown, escalate=False (never conflated with escalation)
        private_query = "phone number of student 22127001"
        priv_res = client.post("/v1/chat", json={"message": private_query})
        assert priv_res.status_code == 200
        priv_body = priv_res.json()
        assert priv_body["intent"] == "unknown"
        assert priv_body["answer"] == PRIVATE_REPLY
        assert priv_body["sources"] == []
        assert priv_body["escalate"] is False
        assert "22127001" not in priv_body["answer"]

        # Deterministic fee & office -> escalate=False
        fee_res = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
        assert fee_res.status_code == 200
        assert fee_res.json()["intent"] == "fee" and "9,450,000 VND" in fee_res.json()["answer"]
        assert fee_res.json()["escalate"] is False

        office_res = client.post("/v1/chat", json={"message": "where is the library"})
        assert office_res.status_code == 200
        assert office_res.json()["intent"] == "office" and "B.201" in office_res.json()["answer"]
        assert office_res.json()["escalate"] is False


def test_chat_degraded_fallback_sets_degraded_true_and_escalate_false(settings) -> None:
    rag_settings = settings.model_copy(update={"rag_enabled": True, "kb_dir": settings.data_dir / "kb"})
    service = create_service(rag_settings)
    assert service.rag is not None
    service.rag.llm = StubLLM(fail=True)
    app = create_app(settings=rag_settings, service=service)

    with TestClient(app) as client:
        res = client.post("/v1/chat", json={"message": "I lost my student card"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "rule"
    assert body["degraded"] is True
    assert body["escalate"] is False
    assert [s["id"] for s in body["sources"]] == ["S26#3"]


def test_legacy_rag_disabled_unknown_does_not_fabricate_escalation(settings) -> None:
    app = create_app(settings=settings)
    with TestClient(app) as client:
        res = client.post("/v1/chat", json={"message": "xyzzy qqqq"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "unknown"
    assert body["escalate"] is False


def test_chat_validation_422_rate_limit_429_and_feedback_contract(rag_app) -> None:
    with TestClient(rag_app) as client:
        bad_empty = client.post("/v1/chat", json={"message": "   "})
        assert bad_empty.status_code == 422
        assert bad_empty.json()["error"]["code"] == "invalid_request"

        bad_long = client.post("/v1/chat", json={"message": "x" * 2001})
        assert bad_long.status_code == 422

        # Send 5 allowed chats (limit=5), then 6th triggers 429
        last_req_id = ""
        for _ in range(5):
            ok = client.post("/v1/chat", json={"message": "hi"})
            assert ok.status_code == 200
            last_req_id = ok.json()["request_id"]

        limited = client.post("/v1/chat", json={"message": "hi"})
        assert limited.status_code == 429

        # Feedback thumbs up & thumbs down succeed with real request_id; unknown returns 404
        up = client.post("/v1/feedback", json={"request_id": last_req_id, "rating": 1})
        assert up.status_code == 201 and up.json()["rating"] == 1

        down = client.post("/v1/feedback", json={"request_id": last_req_id, "rating": -1})
        assert down.status_code == 201 and down.json()["rating"] == -1

        missing = client.post("/v1/feedback", json={"request_id": "unknown-id", "rating": 1})
        assert missing.status_code == 404


def test_starter_ui_client_is_compatible_with_fastapi_contract(rag_app) -> None:
    with TestClient(rag_app) as http_client:
        def forward(request: httpx.Request) -> httpx.Response:
            res = http_client.request(
                request.method,
                request.url.path,
                content=request.content,
                headers=dict(request.headers),
            )
            return httpx.Response(res.status_code, content=res.content, headers=dict(res.headers))

        api = AssistantClient("http://testserver", transport=httpx.MockTransport(forward))
        assert api.healthy() is True

        rule = api.ask("I lost my student card", "tab-1")
        assert rule.ok is True and rule.escalate is False and rule.degraded is False
        assert [s["id"] for s in rule.sources] == ["S26#3"]
        assert api.send_feedback(rule.request_id, -1) is True

        oos = api.ask("what is the capital of France", "tab-1")
        assert oos.ok is True and oos.escalate is True

        priv = api.ask("what grade did my friend get", "tab-1")
        assert priv.ok is True and priv.escalate is False
