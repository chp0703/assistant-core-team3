from __future__ import annotations

import json
from pathlib import Path

import pytest

from assistant_core.guard import is_private_request
from assistant_core.llm import StubLLM
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index

LAB_ROOT = Path(__file__).parents[1]
REPO_ROOT = LAB_ROOT.parent
CASES_PATH = LAB_ROOT / "eval" / "cases.jsonl"
STARTER_PATH = REPO_ROOT / "public_materials" / "lab06" / "starter" / "eval" / "cases.jsonl"
KB_DIR = LAB_ROOT / "data" / "kb"
EXPECTATION_KEYS = {"expect_source", "expect_contains", "expect_abstain"}


def load_cases() -> tuple[list[str], list[dict]]:
    lines = CASES_PATH.read_text(encoding="utf-8").splitlines()
    return lines, [json.loads(line) for line in lines]


def test_eval_cases_have_valid_shape_and_continuous_unique_ids() -> None:
    lines, cases = load_cases()

    assert len(lines) == 25
    assert [case["id"] for case in cases] == [f"E{number:02d}" for number in range(1, 26)]
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert {"id", "question", "category"} <= case.keys()
        assert len(EXPECTATION_KEYS & case.keys()) == 1


def test_first_twenty_cases_match_starter_when_available() -> None:
    if STARTER_PATH.exists():
        lines, _ = load_cases()
        assert lines[:20] == STARTER_PATH.read_text(encoding="utf-8").splitlines()


def test_h1_cases_have_contract_distribution() -> None:
    _, cases = load_cases()
    h1_cases = cases[20:]

    assert [case["id"] for case in h1_cases] == ["E21", "E22", "E23", "E24", "E25"]
    assert sum("expect_source" in case for case in h1_cases) == 3
    assert sum(case.get("expect_abstain") is True for case in h1_cases) == 2
    assert h1_cases[3]["category"] == "privacy"
    assert h1_cases[4]["category"] == "out-of-scope"


def test_all_expected_sources_exist_in_knowledge_base() -> None:
    _, cases = load_cases()
    chunk_ids = {chunk.id for chunk in load_folder(KB_DIR)}
    expected_sources = {case["expect_source"] for case in cases if "expect_source" in case}

    assert expected_sources <= chunk_ids


@pytest.fixture(scope="module")
def h1_answerer() -> RagAnswerer:
    chunks = load_folder(KB_DIR)
    return RagAnswerer(make_index("bm25", chunks), StubLLM())


@pytest.mark.parametrize(
    ("case_id", "expected_source"),
    [("E21", "H26#5.4"), ("E22", "H26#8.3"), ("E23", "S26#1")],
)
def test_h1_normal_cases_return_expected_source(
    h1_answerer: RagAnswerer,
    case_id: str,
    expected_source: str,
) -> None:
    _, cases = load_cases()
    case = next(case for case in cases if case["id"] == case_id)

    result = h1_answerer.answer(case["question"])

    assert result.path != "abstain"
    assert [source.id for source in result.sources] == [expected_source]


def test_h1_privacy_case_is_blocked_before_answering(h1_answerer: RagAnswerer) -> None:
    _, cases = load_cases()
    case = next(case for case in cases if case["id"] == "E24")

    assert is_private_request(case["question"])
    result = h1_answerer.answer(case["question"])
    assert result.path == "abstain"
    assert result.sources == ()


def test_h1_out_of_scope_case_abstains_and_escalates(h1_answerer: RagAnswerer) -> None:
    _, cases = load_cases()
    case = next(case for case in cases if case["id"] == "E25")

    result = h1_answerer.answer(case["question"])

    assert result.path == "abstain"
    assert result.escalate is True
    assert result.sources == ()
