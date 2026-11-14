"""Real Part C + Part D handoff checks; run after those dependencies are available."""

from pathlib import Path

import pytest

from assistant_core import llm
from assistant_core.models import Intent
from assistant_core.rag import answerer, chunker, index

pytestmark = pytest.mark.skipif(
    not hasattr(llm, "StubLLM") or not hasattr(index, "make_index"),
    reason="Part C retrieval and Part D/A2 are not both merged into main yet",
)
KB = Path(__file__).resolve().parents[1] / "data" / "kb"


@pytest.fixture
def bm25():
    return index.make_index("bm25", chunker.load_folder(KB))


@pytest.mark.parametrize("provider", [None, "stub"])
def test_real_retrieval_cites_student_card_rule(bm25, provider):
    model = llm.StubLLM() if provider else None
    result = answerer.RagAnswerer(bm25, model).answer("I lost my student card")
    assert result.path == ("llm" if provider else "retrieval")
    assert result.intent is Intent.RULE and [s.id for s in result.sources] == ["S26#3"]
    assert not result.degraded


@pytest.mark.parametrize("failure", ["fail", "garbage"])
def test_real_stub_failure_falls_back_to_original_kb(bm25, failure):
    result = answerer.RagAnswerer(bm25, llm.StubLLM(**{failure: True})).answer("I lost my student card")
    assert result.path == "retrieval" and result.degraded
    assert [s.id for s in result.sources] == ["S26#3"]
    assert "replacement fee is 50,000 VND" in result.answer


def test_real_bm25_unrelated_query_abstains(bm25):
    result = answerer.RagAnswerer(bm25, llm.StubLLM()).answer("what is the capital of France")
    assert result.path == "abstain" and result.escalate and result.sources == ()
