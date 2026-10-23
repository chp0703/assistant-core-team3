"""Characterize the public model contract from Lab 3, Steps 4 and B.2."""

import pytest
from pydantic import ValidationError

from assistant_core.models import Intent, Message, Response, Source


@pytest.mark.parametrize("length", [1, 2000])
def test_message_accepts_text_length_boundaries(length: int) -> None:
    message = Message(text="a" * length)

    assert len(message.text) == length
    assert message.session_id == "local"


@pytest.mark.parametrize("text", ["", "a" * 2001, None, 123, False, [], {}, b"\xff"])
def test_message_rejects_invalid_text(text: object) -> None:
    with pytest.raises(ValidationError) as caught:
        Message.model_validate({"text": text})

    assert caught.value.errors()[0]["loc"] == ("text",)


def test_message_requires_text() -> None:
    with pytest.raises(ValidationError):
        Message.model_validate({})


def test_message_normalizes_text_without_changing_session() -> None:
    message = Message(text=" \tXin chào  bạn!\n ", session_id=" student-01 ")

    assert message.text == "Xin chào  bạn!"
    assert message.session_id == " student-01 "


@pytest.mark.parametrize("text", [" ", "\t\n\r", "\u00a0", "\u2003", b" \t\n"])
def test_message_rejects_whitespace_only_text(text: object) -> None:
    with pytest.raises(ValidationError) as caught:
        Message.model_validate({"text": text})

    assert caught.value.errors()[0]["loc"] == ("text",)


@pytest.mark.parametrize("length", [1, 2000])
def test_message_checks_length_after_normalization(length: int) -> None:
    message = Message(text="\t " + "a" * length + " \n")

    assert message.text == "a" * length


def test_message_rejects_overlong_normalized_text() -> None:
    with pytest.raises(ValidationError):
        Message(text=" " + "a" * 2001 + " ")


def test_message_normalizes_utf8_bytes_after_decoding() -> None:
    message = Message.model_validate({"text": b"  hello \n"})

    assert message.text == "hello"


def test_normalized_unicode_message_survives_json_round_trip() -> None:
    message = Message(text="\u00a0 Xin  chào 👋 \u2003")

    assert message.text == "Xin  chào 👋"
    assert Message.model_validate_json(message.model_dump_json()) == message


def test_normalization_is_limited_to_message_text() -> None:
    source = Source(id=" H26-5.3 ", title=" Thesis registration ")
    response = Response(answer=" A rule. ", intent=Intent.RULE, sources=[source])

    assert response.answer == " A rule. "
    assert response.sources[0].id == " H26-5.3 "
    assert response.sources[0].title == " Thesis registration "


@pytest.mark.parametrize(
    ("intent", "wire_value"),
    [
        (Intent.GREETING, "greeting"),
        (Intent.FEE, "fee"),
        (Intent.OFFICE, "office"),
        (Intent.RULE, "rule"),
        (Intent.UNKNOWN, "unknown"),
    ],
)
def test_response_intent_json_contract(intent: Intent, wire_value: str) -> None:
    response = Response.model_validate({"answer": "An answer.", "intent": wire_value})

    assert response.intent is intent
    assert response.model_dump(mode="json") == {
        "answer": "An answer.",
        "intent": wire_value,
        "sources": [],
        "degraded": False,
    }
    assert Response.model_validate_json(response.model_dump_json()) == response


def test_response_validates_nested_sources_and_fallback_status() -> None:
    response = Response.model_validate(
        {
            "answer": "Template answer.",
            "intent": Intent.RULE,
            "sources": [{"id": "H26-5.3", "title": "Thesis registration"}],
            "degraded": True,
        }
    )

    assert response.sources == [Source(id="H26-5.3", title="Thesis registration")]
    assert response.degraded is True
    assert Response.model_validate_json(response.model_dump_json()) == response


def test_response_source_lists_are_independent() -> None:
    first = Response(answer="First answer.", intent=Intent.RULE)
    second = Response(answer="Second answer.", intent=Intent.UNKNOWN)

    first.sources.append(Source(id="H26-5.3", title="Thesis registration"))

    assert second.sources == []


@pytest.mark.parametrize("missing_field", ["id", "title"])
def test_source_requires_reference_fields(missing_field: str) -> None:
    values = {"id": "H26-5.3", "title": "Thesis registration"}
    del values[missing_field]

    with pytest.raises(ValidationError) as caught:
        Source(**values)

    assert caught.value.errors()[0]["loc"] == (missing_field,)


@pytest.mark.parametrize("missing_field", ["answer", "intent"])
def test_response_requires_answer_and_intent(missing_field: str) -> None:
    values = {"answer": "Hello!", "intent": "greeting"}
    del values[missing_field]

    with pytest.raises(ValidationError):
        Response.model_validate(values)


def test_response_rejects_unsupported_intent() -> None:
    with pytest.raises(ValidationError) as caught:
        Response.model_validate({"answer": "Hello!", "intent": "unsupported"})

    assert caught.value.errors()[0]["loc"] == ("intent",)


def test_response_rejects_incomplete_nested_source() -> None:
    with pytest.raises(ValidationError) as caught:
        Response.model_validate({"answer": "A rule.", "intent": Intent.RULE, "sources": [{"id": "H26-5.3"}]})

    assert caught.value.errors()[0]["loc"] == ("sources", 0, "title")
