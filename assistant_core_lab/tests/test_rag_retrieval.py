"""Tests for Lab 06 Part C knowledge loading and retrieval."""

import math
from pathlib import Path

import pytest

from assistant_core.rag.chunker import Chunk, load_folder
from assistant_core.rag.index import Hit, make_index

KB = Path(__file__).resolve().parents[1] / "data" / "kb"


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    return load_folder(KB)


def test_sample_knowledge_base_loads_with_stable_metadata(chunks: list[Chunk]) -> None:
    assert len(chunks) == 14
    assert chunks == load_folder(KB)

    thesis = next(chunk for chunk in chunks if chunk.id == "H26#5.3")
    assert thesis.doc_id == "H26"
    assert thesis.title == "5.3 Thesis registration"
    assert thesis.version == "2026.1"
    assert thesis.owner == "Training Office"
    assert "at least 120 accumulated credits" in thesis.text


def test_empty_knowledge_base_returns_no_chunks(tmp_path: Path) -> None:
    assert load_folder(tmp_path) == []


@pytest.mark.parametrize("kind", ["bm25", "tfidf", "hybrid"])
def test_supported_indexes_find_thesis_rule(chunks: list[Chunk], kind: str) -> None:
    hits = make_index(kind, chunks).search("can I register my thesis with 118 credits", 2)

    assert hits[0].chunk.id == "H26#5.3"


def test_bm25_finds_student_card_service(chunks: list[Chunk]) -> None:
    hits = make_index("bm25", chunks).search("How do I replace a lost student card?")

    assert hits[0].chunk.id == "S26#3"


def test_bm25_returns_no_hits_for_unrelated_question(chunks: list[Chunk]) -> None:
    assert make_index("bm25", chunks).search("What is the capital of France?") == []


def test_bm25_results_are_bounded_valid_and_deterministic(chunks: list[Chunk]) -> None:
    index = make_index("bm25", chunks)
    first = index.search("credits registration week", 2)

    assert first == index.search("credits registration week", 2)
    assert len(first) <= 2
    assert all(isinstance(hit, Hit) for hit in first)
    assert all(hit.chunk.id and math.isfinite(hit.score) and hit.score > 0 for hit in first)
    assert [hit.score for hit in first] == sorted((hit.score for hit in first), reverse=True)


def test_bm25_excludes_zero_scores_and_handles_empty_index(chunks: list[Chunk]) -> None:
    assert make_index("bm25", []).search("thesis") == []
    assert make_index("bm25", chunks).search("thesis", 0) == []
    assert all(hit.score > 0 for hit in make_index("bm25", chunks).search("thesis", len(chunks)))
