from types import SimpleNamespace

import pytest

import assistant_core.errors as errors
from assistant_core.responder import StubLLMResponder, TemplateResponder


@pytest.fixture
def rule() -> SimpleNamespace:
    return SimpleNamespace(title="Credit limit", text="Students may take 30 credits.")


def test_template_responder_formats_rule(rule: SimpleNamespace) -> None:
    answer = TemplateResponder().explain("How many credits?", rule)

    assert answer == "Credit limit: Students may take 30 credits."


def test_stub_responder_returns_deterministic_answer(rule: SimpleNamespace) -> None:
    answer = StubLLMResponder().explain("How many credits?", rule)

    assert answer == "Based on 'Credit limit': Students may take 30 credits."


def test_stub_responder_raises_provider_error_on_failure(
    monkeypatch: pytest.MonkeyPatch, rule: SimpleNamespace
) -> None:
    class ProviderError(errors.AssistantError):
        pass

    monkeypatch.setattr(errors, "ProviderError", ProviderError, raising=False)

    with pytest.raises(ProviderError, match="stub provider unavailable"):
        StubLLMResponder(fail=True).explain("How many credits?", rule)
