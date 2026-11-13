"""Unit tests for the shared Lab 06 RAG result contract."""

from dataclasses import FrozenInstanceError
from typing import get_args

import pytest

from assistant_core.models import Intent, Source
from assistant_core.rag import RagPath, RagResult
from assistant_core.rag.types import RagPath as DirectRagPath
from assistant_core.rag.types import RagResult as DirectRagResult


def test_rag_exports_match_types_module() -> None:
    assert RagPath is DirectRagPath
    assert RagResult is DirectRagResult
    assert set(get_args(RagPath)) == {"retrieval", "llm", "abstain", "tool"}


def test_rag_result_defaults_and_immutability() -> None:
    result = RagResult(answer="Sample answer.", intent=Intent.RULE)

    assert result.sources == ()
    assert result.path == "retrieval"
    assert result.degraded is False
    assert result.escalate is False
    assert result.confidence is None

    with pytest.raises(FrozenInstanceError):
        result.answer = "Mutated"  # type: ignore[misc]


def test_rag_result_full_fields() -> None:
    src = Source(id="H26#5.3", title="5.3 Thesis registration")
    result = RagResult(
        answer="Grounded rule answer.",
        intent=Intent.RULE,
        sources=(src,),
        path="llm",
        degraded=False,
        escalate=False,
        confidence=0.85,
    )

    assert result.sources == (src,)
    assert result.path == "llm"
    assert result.confidence == pytest.approx(0.85)
