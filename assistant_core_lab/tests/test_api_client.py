"""Unit tests for the Streamlit HTTP API client."""

from __future__ import annotations

import json

import httpx
import pytest

from ui.api_client import AssistantClient

CHAT_RESPONSE = {
    "answer": "Contact Student Services in room A.101.",
    "intent": "rule",
    "sources": [{"id": "S26#3", "title": "3 Student card replacement"}],
    "degraded": False,
    "escalate": False,
    "request_id": "request-123",
}


def make_client(handler) -> AssistantClient:
    return AssistantClient("http://api.test", transport=httpx.MockTransport(handler))


def test_ask_sends_payload_and_preserves_success_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat"
        assert json.loads(request.content) == {"message": "I lost my student card", "session_id": "session-123"}
        return httpx.Response(200, json=CHAT_RESPONSE)

    result = make_client(handler).ask("I lost my student card", "session-123")

    assert result.ok is True
    assert result.answer == CHAT_RESPONSE["answer"]
    assert result.intent == "rule"
    assert result.sources == [{"id": "S26#3", "title": "3 Student card replacement"}]
    assert result.request_id == "request-123"
    assert result.path == ""


@pytest.mark.parametrize(
    ("field", "value"),
    [("escalate", True), ("degraded", True)],
)
def test_ask_preserves_status_flags(field: str, value: bool) -> None:
    response = {**CHAT_RESPONSE, field: value}

    result = make_client(lambda _: httpx.Response(200, json=response)).ask("question", "session")

    assert result.ok is True
    assert getattr(result, field) is value


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (httpx.ReadTimeout("timed out"), "taking too long"),
        (httpx.ConnectError("refused"), "Cannot reach"),
    ],
)
def test_ask_handles_network_errors(exception: httpx.HTTPError, message: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        exception.request = request
        raise exception

    result = make_client(handler).ask("question", "session")

    assert result.ok is False
    assert message in result.error


@pytest.mark.parametrize(
    ("status_code", "message"),
    [(422, "type a question"), (429, "Too many questions"), (500, "error 500")],
)
def test_ask_handles_http_errors(status_code: int, message: str) -> None:
    result = make_client(lambda _: httpx.Response(status_code)).ask("question", "session")

    assert result.ok is False
    assert message in result.error


def test_ask_handles_invalid_json() -> None:
    result = make_client(lambda _: httpx.Response(200, content=b"not-json")).ask("question", "session")

    assert result.ok is False
    assert result.error == "The assistant returned an invalid response. Please try again."


@pytest.mark.parametrize(
    "response",
    [
        {key: value for key, value in CHAT_RESPONSE.items() if key != "answer"},
        {**CHAT_RESPONSE, "sources": "S26#3"},
        {**CHAT_RESPONSE, "sources": [{"id": "S26#3"}]},
        {**CHAT_RESPONSE, "escalate": "yes"},
        {**CHAT_RESPONSE, "degraded": 1},
        {**CHAT_RESPONSE, "request_id": None},
    ],
)
def test_ask_rejects_missing_or_malformed_fields(response: dict) -> None:
    result = make_client(lambda _: httpx.Response(200, json=response)).ask("question", "session")

    assert result.ok is False
    assert result.error == "The assistant returned an invalid response. Please try again."


@pytest.mark.parametrize("rating", [-1, 0, 1])
def test_send_feedback_accepts_supported_ratings(rating: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/feedback"
        assert json.loads(request.content) == {"request_id": "request-123", "rating": rating, "comment": "Useful"}
        return httpx.Response(201)

    assert make_client(handler).send_feedback("request-123", rating, "Useful") is True


@pytest.mark.parametrize("outcome", [httpx.Response(404), httpx.ReadTimeout("timed out")])
def test_send_feedback_handles_failure(outcome: httpx.Response | httpx.HTTPError) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(outcome, httpx.HTTPError):
            outcome.request = request
            raise outcome
        return outcome

    assert make_client(handler).send_feedback("request-123", -1) is False


def test_healthy_returns_true_for_200() -> None:
    assert make_client(lambda _: httpx.Response(200)).healthy() is True


@pytest.mark.parametrize("outcome", [httpx.Response(503), httpx.ReadTimeout("timed out")])
def test_healthy_handles_failure(outcome: httpx.Response | httpx.HTTPError) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(outcome, httpx.HTTPError):
            outcome.request = request
            raise outcome
        return outcome

    assert make_client(handler).healthy() is False
