"""Lab 08 H1 edge-case review for Phat's service execution path."""

import pytest

from assistant_core.models import Intent


def test_execute_empty_text_returns_unknown_without_rag(service):
    response, rag_result = service._execute("")

    assert response.intent is Intent.UNKNOWN
    assert rag_result is None


def test_execute_zero_credit_request_keeps_fee_validation_in_the_tool(service):
    response, rag_result = service._execute("tuition for 0 credits")

    assert response.intent is Intent.FEE
    assert "Credits must be between 1 and 30." in response.answer
    assert rag_result is None


def test_execute_large_text_does_not_bypass_message_boundary(service):
    response, rag_result = service._execute("x" * 5000)

    assert response.intent is Intent.UNKNOWN
    assert rag_result is None


def test_execute_vietnamese_fee_uses_deterministic_calculation(service):
    response, rag_result = service._execute("Tính học phí cho 18 tín chỉ")

    assert response.intent is Intent.FEE
    assert "8,100,000 VND" in response.answer
    assert rag_result is None


@pytest.mark.parametrize("text", [None, 42, b"tuition"])
def test_execute_rejects_non_string_text_with_type_error(service, text):
    with pytest.raises(TypeError):
        service._execute(text)


def test_execute_greeting_control_remains_deterministic(service):
    response, rag_result = service._execute("  HI! ")

    assert response.intent is Intent.GREETING
    assert response.answer.startswith("Hello!")
    assert rag_result is None
