"""Deterministic input guards, before retrieval and model calls."""

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

INJECTION_PATTERNS = (
    re.compile(r"\bignore (?:all |any |the )?(?:previous|above|prior|earlier) (?:instructions|rules|messages)\b"),
    re.compile(r"\b(?:reveal|show|print|repeat) (?:me )?(?:your|the) (?:system )?(?:prompt|instructions|rules)\b"),
    re.compile(r"\byou are now\b"),
    re.compile(r"\b(?:developer|debug|admin|god) mode\b"),
    re.compile(r"\bpretend (?:to be|you are)\b"),
)
INJECTION_REPLY = (
    "I can only answer questions about fees, offices and the student handbook, and I can't change my rules."
)


def looks_like_injection(text: str) -> bool:
    """Match known prompt-injection patterns in user messages."""
    if not isinstance(text, str):
        raise TypeError("Message text must be a string")
    normalized = " ".join(text.casefold().split())
    return any(pattern.search(normalized) for pattern in INJECTION_PATTERNS)


def is_private_request(text: str) -> bool:
    """Recognize starter-style third-party record requests in English/Vietnamese."""
    normalized = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())
    # shortcut: any eight-digit ID is private, refine with authenticated identity if records are added.
    return bool(
        re.search(r"\b\d{8}\b", normalized) or (re.search(_RECORD, normalized) and re.search(_OTHER, normalized))
    )
