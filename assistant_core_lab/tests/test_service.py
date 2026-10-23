import logging
from pathlib import Path

import pytest

from assistant_core.config import Settings
from assistant_core.errors import ConfigError, DataError, ProviderError
from assistant_core.knowledge import Rule
from assistant_core.models import Intent, Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService, create_service


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def service(data_dir: Path) -> AssistantService:
    return create_service(Settings(data_dir=data_dir))


@pytest.mark.parametrize(
    ("text", "intent", "fragment"),
    [
        ("hi", Intent.GREETING, "Hello!"),
        ("tuition for 18 credits and 2 retake", Intent.FEE, "9,450,000 VND"),
        ("where is the library", Intent.OFFICE, "B.201"),
        ("thesis registration credits", Intent.RULE, "120 accumulated credits"),
        ("xyzzy qqqq", Intent.UNKNOWN, "don't know"),
    ],
)
def test_service_dispatch(service: AssistantService, text: str, intent: Intent, fragment: str) -> None:
    response = service.handle(Message(text=text))
    assert response.intent is intent and fragment in response.answer
    assert not response.degraded
    assert bool(response.sources) is (intent is Intent.RULE)


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ("fee", "How many credits?"),
        ("fee 40 credits", "between 1 and 30"),
    ],
)
def test_invalid_fee_is_a_user_facing_response(service: AssistantService, text: str, fragment: str) -> None:
    response = service.handle(Message(text=text))
    assert response.intent is Intent.FEE and fragment in response.answer
    assert response.sources == [] and not response.degraded


def test_fallback_keeps_source_and_marks_degraded(service: AssistantService) -> None:
    service.responder = StubLLMResponder(fail=True)
    response = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert response.degraded and response.sources[0].id == "H26-5.3"
    assert "120 accumulated credits" in response.answer


def test_provider_details_and_user_text_are_not_logged(service: AssistantService, caplog) -> None:
    secret = "private-key-canary"
    question = "thesis registration private-message-canary"

    class LeakyProvider:
        def explain(self, question: str, rule: Rule) -> str:
            raise ProviderError(f"{secret}: {question}")

    service.responder = LeakyProvider()
    with caplog.at_level(logging.INFO, logger="assistant_core"):
        response = service.handle(Message(text=question, session_id="session-1"))
    assert response.degraded
    assert "provider failed" in caplog.text
    assert secret not in caplog.text and question not in caplog.text
    handled = next(record for record in caplog.records if record.msg == "handled")
    assert handled.intent == "rule" and handled.session == "session-1" and handled.degraded
    assert handled.latency_ms >= 0


def test_service_respects_configured_fees(service: AssistantService) -> None:
    service.settings = Settings(credit_rate_vnd=500_000, retake_multiplier=2.0, max_credits=24)
    assert "7,000,000 VND" in service.handle(Message(text="fee 10 credits and 2 retake")).answer
    assert "between 1 and 24" in service.handle(Message(text="fee 25 credits")).answer


def test_no_match_does_not_call_provider(service: AssistantService) -> None:
    class UnexpectedProvider:
        def explain(self, question: str, rule: Rule) -> str:
            raise AssertionError("No provider call expected without a matching source.")

    service.responder = UnexpectedProvider()
    assert service.handle(Message(text="xyzzy qqqq")).intent is Intent.UNKNOWN


def test_startup_missing_data_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(DataError):
        create_service(Settings(data_dir=tmp_path))


def test_unsupported_provider_does_not_silently_use_stub(data_dir: Path) -> None:
    with pytest.raises(ConfigError, match="Unsupported LLM_PROVIDER"):
        create_service(Settings(data_dir=data_dir, llm_provider="remote", llm_api_key="test-key"))


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("tuition for 18 credits and 2 retake", "9,450,000"),
        ("fee 2 retake and 18 credits", "9,450,000"),
        ("fee 30 credits", "13,500,000"),
    ],
)
def test_reference_tuition_amounts(service: AssistantService, text: str, amount: str) -> None:
    assert service.handle(Message(text=text)).answer == f"Your tuition is {amount} VND."
