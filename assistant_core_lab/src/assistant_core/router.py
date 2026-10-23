"""Deterministic request-intent routing."""

import re
import unicodedata

from assistant_core.models import Intent

GREETINGS = frozenset({"hi", "hello", "hey", "xin chao"})


def _normalize_text(text: str) -> str:
    """Normalize user text for deterministic intent matching."""
    normalized = unicodedata.normalize("NFC", text).casefold().strip().rstrip("?!.")
    return " ".join(normalized.split())


def route(text: str, office_names: set[str]) -> Intent:
    """Determine the intent of a user question."""
    t = _normalize_text(text)

    if t in GREETINGS:
        return Intent.GREETING

    if "fee" in t or "tuition" in t or re.search(r"\bhọc phí\b", t):
        return Intent.FEE

    if any(name in t for name in office_names):
        return Intent.OFFICE

    return Intent.RULE
