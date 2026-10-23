"""Tests for deterministic tuition tools."""

import unicodedata

import pytest

from assistant_core.errors import InvalidRequest
from assistant_core.tools import parse_credits, tuition


def test_parse_with_retake():
    assert parse_credits("tuition for 18 credits and 2 retake") == (18, 2)


def test_parse_without_retake():
    assert parse_credits("tuition for 12 credits") == (12, 0)


@pytest.mark.parametrize(
    "text",
    [
        "Học phí cho 18 tín chỉ và 2 tín chỉ học lại",
        "  HỌC PHÍ cho 18  TÍN   CHỈ và 2 tín chỉ HỌC LẠI  ",
        unicodedata.normalize("NFD", "Học phí cho 18 tín chỉ và 2 tín chỉ học lại"),
    ],
)
def test_parse_vietnamese_credits(text):
    assert parse_credits(text) == (18, 2)


def test_parse_vietnamese_reversed_order():
    assert parse_credits("Học phí cho 2 tín chỉ học lại và 18 tín chỉ") == (18, 2)


def test_parse_vietnamese_missing_regular_credits():
    with pytest.raises(InvalidRequest, match="How many credits"):
        parse_credits("Học phí cho 2 tín chỉ học lại")


@pytest.mark.parametrize(
    "text",
    [
        "Học phí năm 2026 cho 18 tín chỉ và 2 tín chỉ học lại",
        "Học phí cho 18 tín chỉ và 20 tín chỉ",
        "Học phí cho 18 tín chỉ, 2 tín chỉ học lại và 3 tín chỉ học lại",
        "Học phí cho 18 tín chỉ và -2 tín chỉ học lại",
        "student 2026 tuition for 18 credits and 2 retake",
    ],
)
def test_parse_rejects_ambiguous_credit_numbers(text):
    with pytest.raises(InvalidRequest, match="ambiguous"):
        parse_credits(text)


def test_parse_english_is_case_insensitive():
    assert parse_credits("TUITION FOR 18 CREDITS AND 2 RETAKE") == (18, 2)


def test_parse_missing_credits():
    with pytest.raises(InvalidRequest, match="How many credits"):
        parse_credits("tuition fee")


def test_tuition_value():
    assert tuition(18, 2, 450_000, 1.5, 30) == 9_450_000


def test_vietnamese_request_tuition_value():
    credits, retake = parse_credits("Học phí cho 18 tín chỉ và 2 tín chỉ học lại")

    assert tuition(credits, retake, 450_000, 1.5, 30) == 9_450_000


def test_tuition_rejects_negative_retake_credits():
    with pytest.raises(InvalidRequest, match="Retake credits"):
        tuition(18, -2, 450_000, 1.5, 30)


@pytest.mark.parametrize("credits", [0, 31])
def test_tuition_out_of_range(credits):
    with pytest.raises(InvalidRequest):
        tuition(credits, 0, 450_000, 1.5, 30)
