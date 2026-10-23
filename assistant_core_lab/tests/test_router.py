"""Tests for deterministic request-intent routing."""

import unicodedata

import pytest

from assistant_core.models import Intent
from assistant_core.router import route


def test_route_greeting():
    assert route("Hello!", set()) == Intent.GREETING


def test_route_fee():
    assert route("tuition for 18 credits", set()) == Intent.FEE


@pytest.mark.parametrize(
    "text",
    [
        "Học phí cho 18 tín chỉ",
        "  HỌC   PHÍ cho 18 tín chỉ  ",
        unicodedata.normalize("NFD", "Học phí cho 18 tín chỉ"),
    ],
)
def test_route_vietnamese_fee(text):
    assert route(text, set()) == Intent.FEE


def test_route_vietnamese_near_match_is_not_fee():
    assert route("Tôi đang học phím đàn", set()) == Intent.RULE


def test_route_office():
    office_names = {"library", "registrar"}
    assert route("Where is the library?", office_names) == Intent.OFFICE


def test_route_rule():
    assert route("Can I register my thesis?", set()) == Intent.RULE
