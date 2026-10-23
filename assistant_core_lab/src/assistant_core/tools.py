"""Deterministic tools for tuition calculation."""

import re
import unicodedata

from assistant_core.errors import InvalidRequest


def _normalize_text(text: str) -> str:
    """Normalize case, Unicode composition, and whitespace for parsing."""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _parse_labelled_credits(text: str, pattern: str) -> tuple[int, int]:
    """Extract one regular count and at most one retake count."""
    matches = list(re.finditer(pattern, text))
    regular = [int(match.group("count")) for match in matches if match.group("retake") is None]
    retake = [int(match.group("count")) for match in matches if match.group("retake") is not None]

    if not regular:
        raise InvalidRequest("How many credits?")

    number_spans = {match.span() for match in re.finditer(r"(?<!\w)-?\d+(?!\w)", text)}
    labelled_spans = {match.span("count") for match in matches}

    if len(regular) != 1 or len(retake) > 1 or number_spans != labelled_spans:
        raise InvalidRequest("Credit information is ambiguous.")

    return regular[0], retake[0] if retake else 0


def parse_credits(text: str) -> tuple[int, int]:
    """Extract regular and retake credits from a tuition question."""
    normalized = _normalize_text(text)

    if any(label in normalized for label in ("học phí", "tín chỉ", "học lại")):
        return _parse_labelled_credits(
            normalized,
            r"(?P<count>\d+)\s+tín\s+chỉ(?P<retake>\s+học\s+lại)?\b",
        )

    return _parse_labelled_credits(
        normalized,
        r"(?P<count>\d+)\s+(?:(?P<retake>retake)(?:\s+credits?)?|credits?\b)",
    )


def tuition(
    credits: int,
    retake: int,
    rate: int,
    retake_multiplier: float,
    max_credits: int,
) -> int:
    """Calculate tuition using configured rates and credit limits."""
    if not 1 <= credits <= max_credits:
        raise InvalidRequest(f"Credits must be between 1 and {max_credits}.")
    if retake < 0:
        raise InvalidRequest("Retake credits cannot be negative.")

    return int(credits * rate + retake * rate * retake_multiplier)
