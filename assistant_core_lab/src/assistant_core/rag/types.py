"""Shared internal RAG types agreed upon by Team 3 for Lab 06 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from assistant_core.models import Intent, Source

RagPath = Literal[
    "retrieval",
    "llm",
    "abstain",
    "tool",
]


@dataclass(frozen=True)
class RagResult:
    """Internal result returned by RAG components before mapping to public Response."""

    answer: str
    intent: Intent
    sources: tuple[Source, ...] = ()
    path: RagPath = "retrieval"
    degraded: bool = False
    escalate: bool = False
    confidence: float | None = None
