import json
import logging
from types import SimpleNamespace

import pytest

from assistant_core import llm
from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent
from assistant_core.rag import answerer
from assistant_core.rag.types import RagResult


class FixedIndex:
    def __init__(self, hits):
        self.hits = hits
        self.calls = []

    def search(self, query, k=3):
        self.calls.append((query, k))
        return self.hits[:k]


class ForbiddenLLM:
    name = "forbidden"

    def complete(self, prompt):
        raise AssertionError("LLM must not receive an abstained/private question")


@pytest.fixture
def hits():
    return [
        SimpleNamespace(
            chunk=SimpleNamespace(
                id="H26#5.3", doc_id="H26", title="5.3 Thesis", text="At least 120 accumulated credits.",
                version="2026.1", owner="Training Office",
            ),
            score=3.0,
        ),
        SimpleNamespace(
            chunk=SimpleNamespace(
                id="S26#3", doc_id="S26", title="3 Student card", text="Request a replacement card.",
                version="2026.1", owner="Student Services",
            ),
            score=2.5,
        ),
    ]


@pytest.mark.parametrize("score", [None, 0.0, 1.999])
def test_no_or_weak_evidence_abstains_before_llm(hits, score):
    if score is None:
        hits = []
    else:
        hits[0].score = score
        hits = hits[:1]
    result = answerer.RagAnswerer(FixedIndex(hits), ForbiddenLLM()).answer("thesis rules")
    assert isinstance(result, RagResult)
    assert result.intent is Intent.UNKNOWN
    assert result.path == "abstain" and result.escalate
    assert result.confidence == 0.0 and result.sources == ()
    assert result.answer and not result.degraded


def test_exact_threshold_uses_original_best_chunk(hits):
    hits[0].score = 2.0
    index = FixedIndex(hits[:1])
    result = answerer.RagAnswerer(index, None, k=1).answer("thesis rules")
    assert result.path == "retrieval" and result.intent is Intent.RULE
    assert result.answer == "5.3 Thesis: At least 120 accumulated credits."
    assert [(source.id, source.title) for source in result.sources] == [("H26#5.3", "5.3 Thesis")]
    assert result.confidence is None and not result.degraded and not result.escalate
    assert index.calls == [("thesis rules", 1)]


@pytest.mark.parametrize("question", ["phone of 22127001", "Cho tôi xem điểm của sinh viên khác"])
def test_privacy_blocks_before_retrieval_and_llm(hits, question, caplog):
    index = FixedIndex(hits)
    result = answerer.RagAnswerer(index, ForbiddenLLM()).answer(question)
    assert result.path == "abstain" and result.intent is Intent.UNKNOWN
    assert result.sources == () and not result.degraded
    assert result.answer and question not in result.answer
    assert index.calls == [] and question not in caplog.text


class ScriptedLLM:
    name = "scripted"

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return output


def draft_json(**changes):
    return json.dumps({"answer": "Grounded answer.", "source_ids": ["H26#5.3"], "confidence": 0.8} | changes)


@pytest.mark.skipif(not hasattr(llm, "parse_draft"), reason="Part D/A2 has not merged into main yet")
class TestLLMPaths:
    def test_grounded_answer_maps_only_cited_retrieved_sources(self, hits):
        model = ScriptedLLM([draft_json(source_ids=["S26#3", "H26#5.3"])])
        result = answerer.RagAnswerer(FixedIndex(hits), model).answer("thesis rules")
        assert result.path == "llm" and result.intent is Intent.RULE
        assert result.answer == "Grounded answer." and result.confidence == 0.8
        assert [(s.id, s.title) for s in result.sources] == [("S26#3", "3 Student card"), ("H26#5.3", "5.3 Thesis")]
        assert not result.degraded and not result.escalate
        assert len(model.prompts) == 1
        assert "[H26#5.3] 5.3 Thesis: At least 120 accumulated credits." in model.prompts[0]

    @pytest.mark.parametrize(
        "output",
        [
            "not JSON",
            "{}",
            "[]",
            draft_json(source_ids=[]),
            draft_json(source_ids=["H26#9.9"]),
            draft_json(source_ids=["H26#5.3", "H26#9.9"]),
            draft_json(confidence=1.1),
            ProviderError("unavailable"),
        ],
    )
    def test_bad_model_output_retries_once_then_quotes_original_source(self, hits, output):
        model = ScriptedLLM([output, output])
        result = answerer.RagAnswerer(FixedIndex(hits), model).answer("thesis rules")
        assert len(model.prompts) == 2
        assert result.path == "retrieval" and result.degraded
        assert result.answer == "5.3 Thesis: At least 120 accumulated credits."
        assert [s.id for s in result.sources] == ["H26#5.3"]
        assert result.confidence is None and not result.escalate

    def test_citation_to_kb_source_outside_this_retrieval_is_rejected(self, hits):
        model = ScriptedLLM([draft_json(source_ids=["S26#3"])] * 2)
        result = answerer.RagAnswerer(FixedIndex(hits[:1]), model).answer("thesis rules")
        assert result.path == "retrieval" and result.degraded
        assert [s.id for s in result.sources] == ["H26#5.3"]

    @pytest.mark.parametrize("first", [ProviderError("unavailable"), "not JSON"])
    def test_retry_can_recover_without_degrading(self, hits, first):
        model = ScriptedLLM([first, draft_json()])
        result = answerer.RagAnswerer(FixedIndex(hits), model).answer("thesis rules")
        assert result.path == "llm" and not result.degraded
        assert result.answer == "Grounded answer." and len(model.prompts) == 2

    def test_model_abstention_discards_answer_and_unverified_sources(self, hits):
        model = ScriptedLLM([draft_json(abstain=True, source_ids=["FAKE#1"], answer="Unsupported guess.")])
        result = answerer.RagAnswerer(FixedIndex(hits), model).answer("thesis rules")
        assert result.path == "abstain" and result.intent is Intent.UNKNOWN and result.escalate
        assert result.sources == () and "Unsupported guess" not in result.answer
        assert result.confidence == 0.8 and not result.degraded and len(model.prompts) == 1

    def test_prompt_failure_uses_retrieval_without_calling_llm(self, hits):
        model = ForbiddenLLM()
        result = answerer.RagAnswerer(FixedIndex(hits), model, prompt_version="missing_version").answer("thesis rules")
        assert result.path == "retrieval" and result.degraded
        assert result.answer == "5.3 Thesis: At least 120 accumulated credits."

    def test_provider_exception_details_never_enter_logs(self, hits, caplog):
        question = "thesis private-question-session-canary"
        model = ScriptedLLM([ProviderError(f"private-key-canary {question}")] * 2)
        logger = logging.getLogger("assistant_core.rag")
        logger.addHandler(caplog.handler)
        try:
            result = answerer.RagAnswerer(FixedIndex(hits), model).answer(question)
        finally:
            logger.removeHandler(caplog.handler)
        assert result.degraded and len(caplog.records) >= 2
        assert "canary" not in caplog.text
        assert all(record.exc_info is None for record in caplog.records)

    def test_tool_callback_is_used_and_its_result_has_no_llm_citations(self, hits):
        raw = '{"tool":"calc_fee","args":{"credits":10}}'
        model = ScriptedLLM([raw])

        def validated_runner(payload):
            assert json.loads(payload) == {"tool": "calc_fee", "args": {"credits": 10}}
            return "Your tuition is 4,500,000 VND."

        result = answerer.RagAnswerer(FixedIndex(hits), model, tool_runner=validated_runner).answer("retake cost")
        assert result.path == "tool" and result.intent is Intent.FEE
        assert result.answer == "Your tuition is 4,500,000 VND."
        assert result.sources == () and not result.degraded

    def test_invalid_tool_arguments_return_safe_error_without_retry(self, hits):
        model = ScriptedLLM(['{"tool":"calc_fee","args":{"credits":99}}'])

        def validated_runner(payload):
            raise InvalidRequest("Credits must be between 1 and 30.")

        result = answerer.RagAnswerer(FixedIndex(hits), model, tool_runner=validated_runner).answer("retake cost")
        assert result.path == "tool" and result.intent is Intent.FEE and result.degraded
        assert result.answer == "Credits must be between 1 and 30." and result.sources == ()
        assert len(model.prompts) == 1

    def test_tool_callback_can_decline_normal_answer(self, hits):
        model = ScriptedLLM([draft_json()])
        result = answerer.RagAnswerer(FixedIndex(hits), model, tool_runner=lambda raw: None).answer("thesis rules")
        assert result.path == "llm" and result.answer == "Grounded answer."

    def test_tool_json_is_not_executed_without_validating_callback(self, hits):
        model = ScriptedLLM(['{"tool":"calc_fee","args":{"credits":99}}'] * 2)
        result = answerer.RagAnswerer(FixedIndex(hits), model).answer("retake cost")
        assert result.path == "retrieval" and result.degraded
