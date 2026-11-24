"""Streamlit chat page (ui/app.py) driven by AppTest, with the HTTP client mocked."""
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from ui.api_client import ChatResult

APP = str(Path(__file__).resolve().parents[1] / "ui" / "app.py")
GOOD = ChatResult(ok=True, answer="Room B.201", intent="office", request_id="req-1",
                  sources=[{"id": "S26#1", "title": "Library borrowing"}])


@pytest.fixture
def client():
    with patch("ui.api_client.AssistantClient") as cls:
        c = cls.return_value
        c.healthy.return_value = True
        c.ask.return_value = GOOD
        c.send_feedback.return_value = True
        yield c


def asked(client) -> AppTest:
    at = AppTest.from_file(APP).run()
    at.chat_input[0].set_value("where is the library").run()
    assert not at.exception
    return at


def test_answer_shows_both_rating_buttons(client):
    at = asked(client)
    assert {b.key for b in at.button if b.key} >= {"up2", "down2"}


def test_thumbs_down_sends_minus_one(client):
    at = asked(client)
    at.button(key="down2").click().run()
    client.send_feedback.assert_called_once_with("req-1", -1)
    assert at.session_state.rated == {"req-1"}
    assert [t.value for t in at.toast] == ["Thanks — we will look at this answer."]


def test_thumbs_up_sends_plus_one(client):
    at = asked(client)
    at.button(key="up2").click().run()
    client.send_feedback.assert_called_once_with("req-1", 1)
    assert at.session_state.rated == {"req-1"}


def test_rated_answer_hides_buttons_on_next_run(client):
    at = asked(client)
    at.button(key="down2").click().run()
    at.run()
    assert not [b for b in at.button if b.key in ("up2", "down2")]


def test_failed_answer_has_no_rating_buttons(client):
    client.ask.return_value = ChatResult(ok=False, error="Cannot reach the assistant.")
    at = asked(client)
    assert not [b for b in at.button if b.key in ("up2", "down2")]


def test_backend_down_shows_error(client):
    client.healthy.return_value = False
    at = AppTest.from_file(APP).run()
    assert len(at.error) == 1


@pytest.mark.parametrize("key, rating", [("up2", 1), ("down2", -1)])
def test_failed_feedback_is_not_reported_as_success(client, key, rating):
    client.send_feedback.return_value = False
    at = asked(client)
    at.button(key=key).click().run()
    client.send_feedback.assert_called_once_with("req-1", rating)
    assert at.session_state.rated == set()
    assert [t.value for t in at.toast] == ["Could not send your feedback. Please try again."]
    assert {"up2", "down2"} <= {b.key for b in at.button}   # buttons stay so the user can retry
