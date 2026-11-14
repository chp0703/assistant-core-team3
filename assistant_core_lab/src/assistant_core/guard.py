"""Deterministic privacy checks, before retrieval and model calls."""

from __future__ import annotations

import re
import unicodedata

_RECORD = (
    r"\b(?:grades?|scores?|gpa|results?|phone|address(?:es)?|emails?|transcripts?|records?|passwords?"
    r"|diem|ket qua|so dien thoai|dia chi|hoc ba|ho so|mat khau)\b"
)
_OTHER = (
    r"\b(?:(?:my|a) (?:friend|classmate|roommate)|(?:another|other) students?"
    r"|sinh vien khac|nguoi khac|ban toi|ban cung lop|ban ay)\b"
)

PRIVATE_REPLY = "I can't share information about other students. You can only see your own records after logging in."


def is_private_request(text: str) -> bool:
    """Recognize starter-style third-party record requests in English/Vietnamese."""
    normalized = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())
    # shortcut: any eight-digit ID is private, refine with authenticated identity if records are added.
    return bool(
        re.search(r"\b\d{8}\b", normalized) or (re.search(_RECORD, normalized) and re.search(_OTHER, normalized))
    )
