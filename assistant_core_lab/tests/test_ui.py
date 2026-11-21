import httpx

from ui.api_client import AssistantClient, ChatResult
from ui.logic import format_sources, status_note, validate_input

OK = {"answer": "Room B.201", "intent": "office", "sources": [{"id": "S26#1", "title": "1 Library borrowing"}],
      "degraded": False, "escalate": False, "path": "deterministic", "request_id": "abc123"}


def client_with(handler) -> AssistantClient:
    return AssistantClient("http://api.test", transport=httpx.MockTransport(handler))


def test_ask_ok():
    r = client_with(lambda req: httpx.Response(200, json=OK)).ask("where is the library", "s1")
    assert r.ok and r.answer == "Room B.201" and r.request_id == "abc123"


def test_ask_backend_down():
    def boom(req):
        raise httpx.ConnectError("refused", request=req)
    r = client_with(boom).ask("hi", "s1")
    assert not r.ok and "backend" in r.error


def test_ask_validation_and_server_errors():
    assert "type a question" in client_with(lambda req: httpx.Response(422)).ask("", "s").error
    assert "error 500" in client_with(lambda req: httpx.Response(500)).ask("x", "s").error


def test_feedback():
    assert client_with(lambda req: httpx.Response(201, json={})).send_feedback("abc123", 1)


def test_validate_input():
    assert validate_input("   ") == "Please type a question."
    assert validate_input("x" * 2001).startswith("Your question is too long")
    assert validate_input("hello") is None


def test_format_sources():
    assert format_sources([]) == ""
    assert format_sources(OK["sources"]) == "Sources: S26#1 — 1 Library borrowing"


def test_status_note():
    assert "Training Office" in status_note(ChatResult(ok=True, escalate=True))
    assert status_note(ChatResult(ok=True)) is None


def test_format_sources_multiple_in_order() -> None:
    sources = [
        {"id": "DOC-101", "title": "Course Registration Guide"},
        {"id": "DOC-204", "title": "Academic Calendar 2026"},
    ]
    assert format_sources(sources) == "Sources: DOC-101 — Course Registration Guide; DOC-204 — Academic Calendar 2026"


def test_format_sources_partial_and_missing_entries() -> None:
    sources = [
        {"id": "DOC-101", "title": ""},
        {"id": "", "title": ""},
        {"title": "Student Handbook"},
        {},
    ]
    assert format_sources(sources) == "Sources: DOC-101; Student Handbook"


def test_format_sources_empty_or_all_blank() -> None:
    assert format_sources([]) == ""
    assert format_sources([{"id": "", "title": ""}, {}]) == ""


def test_status_note_degraded_and_escalation_messages() -> None:
    degraded_result = ChatResult(ok=True, intent="registration", escalate=False, degraded=True)
    assert status_note(degraded_result) == "Shown directly from the source document (the AI helper was unavailable)."

    escalated_result = ChatResult(ok=True, intent="unknown", escalate=True, degraded=False)
    assert status_note(escalated_result) == (
        "I could not find this in the official documents. A staff member can help: Training Office, room I.101."
    )


def test_status_note_escalation_precedence() -> None:
    both_result = ChatResult(ok=True, intent="tuition", escalate=True, degraded=True)
    assert status_note(both_result) == (
        "I could not find this in the official documents. A staff member can help: Training Office, room I.101."
    )


def test_status_note_none_for_unknown_intent_without_flags() -> None:
    normal_result = ChatResult(ok=True, intent="unknown", escalate=False, degraded=False)
    assert status_note(normal_result) is None
