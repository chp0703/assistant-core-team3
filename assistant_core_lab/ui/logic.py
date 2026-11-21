"""UI logic without Streamlit, so it can be unit-tested."""
from __future__ import annotations

from ui.api_client import ChatResult

WELCOME = ("Hi! I can answer questions about fees, offices and the student handbook. "
           "Ask one question at a time. "
           "Try: “Can I register my thesis with 118 credits?”")
EXAMPLES = ["Can I register my thesis with 118 credits?", "Tuition for 18 credits and 2 retake",
            "Where is the library?", "I lost my student card"]


def validate_input(text: str) -> str | None:
    """Return an error message for bad input, or None if it is fine."""
    t = text.strip()
    if not t:
        return "Please type a question."
    if len(t) > 2000:
        return "Your question is too long (max 2000 characters)."
    return None


def format_sources(sources: list[dict]) -> str:
    """Format source entries into a single-line citation string."""
    parts: list[str] = []
    for entry in sources:
        source_id = entry.get("id", "")
        title = entry.get("title", "")
        if source_id and title:
            parts.append(f"{source_id} — {title}")
        elif source_id:
            parts.append(source_id)
        elif title:
            parts.append(title)
    if not parts:
        return ""
    return "Sources: " + "; ".join(parts)


def status_note(result: ChatResult) -> str | None:
    """Return a status note for escalated or degraded chat results."""
    if result.escalate:
        return "I could not find this in the official documents. A staff member can help: Training Office, room I.101."
    if result.degraded:
        return "Shown directly from the source document (the AI helper was unavailable)."
    return None
