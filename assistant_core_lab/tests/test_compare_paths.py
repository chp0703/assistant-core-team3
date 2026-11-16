"""Part F: the comparison runner measures all three paths on the same Lab 06 cases."""

import importlib.util
from pathlib import Path

import pytest

from assistant_core.config import Settings

EVAL = Path(__file__).resolve().parents[1] / "eval"
spec = importlib.util.spec_from_file_location("compare_paths", EVAL / "compare_paths.py")
compare_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_paths)


@pytest.fixture(scope="module")
def rows():
    data = EVAL.parent / "data"
    settings = Settings(data_dir=data, kb_dir=data / "kb")
    return compare_paths.run(settings, compare_paths.load_cases())


def test_three_paths_share_the_same_25_cases(rows):
    assert [r["path"] for r in rows] == ["deterministic", "retrieval", "llm (stub)"]
    assert {r["total"] for r in rows} == {25}
    assert all(r["abstain_total"] == 7 for r in rows)


def test_measurements_are_consistent(rows):
    for r in rows:
        assert r["correct"] + len(r["failures"]) == r["total"]
        assert 0 < r["p50_ms"] <= r["max_ms"]


def test_retrieval_answers_regulation_questions_the_deterministic_path_cannot(rows):
    deterministic, retrieval, _ = rows
    assert retrieval["correct"] > deterministic["correct"]
