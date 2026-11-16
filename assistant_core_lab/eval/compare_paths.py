#!/usr/bin/env python3
"""Lab 06 Part F: compare the deterministic, retrieval and LLM paths on eval/cases.jsonl.

deterministic - router + tools only; rule questions are not answered
retrieval     - router + tools + BM25 retrieval, quoting the best source (no LLM)
llm           - router + tools + the same BM25 retrieval + LLM with structured output (stub by default)

Run from assistant_core_lab/:  python eval/compare_paths.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from assistant_core.config import Settings, load_settings
from assistant_core.knowledge import load_knowledge
from assistant_core.llm import make_llm
from assistant_core.models import Intent, Message
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index
from assistant_core.responder import TemplateResponder
from assistant_core.service import AssistantService

CASES = Path(__file__).with_name("cases.jsonl")


class NoRetrieval:
    """Deterministic path: never answers a regulation question from documents."""

    def search(self, query, k=3):
        return []


def is_correct(case: dict, response) -> bool:
    if case.get("expect_abstain"):
        return response.intent is Intent.UNKNOWN
    if "expect_contains" in case:
        return case["expect_contains"] in response.answer
    return any(source.id == case["expect_source"] for source in response.sources)


def load_cases(path: Path = CASES) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_paths(settings: Settings) -> dict[str, AssistantService]:
    """Three services sharing the same knowledge, index, threshold and responder."""
    knowledge = load_knowledge(settings.data_dir)
    index = make_index(settings.retrieval_kind, load_folder(settings.kb_dir))
    provider = "stub" if settings.llm_provider == "template" else settings.llm_provider
    llm = make_llm(provider, settings.llm_model, settings.llm_base_url, settings.llm_api_key, settings.llm_timeout_s)
    rags = {
        "deterministic": RagAnswerer(NoRetrieval(), None, settings.retrieval_min_score),
        "retrieval": RagAnswerer(index, None, settings.retrieval_min_score),
        f"llm ({llm.name})": RagAnswerer(
            index, llm, settings.retrieval_min_score, prompt_version=settings.prompt_version
        ),
    }
    return {name: AssistantService(settings, knowledge, TemplateResponder(), rag) for name, rag in rags.items()}


def run(settings: Settings, cases: list[dict]) -> list[dict]:
    rows = []
    for name, service in build_paths(settings).items():
        correct = abstain_ok = abstain_total = 0
        latencies, failures = [], []
        for case in cases:
            start = time.perf_counter()
            response = service.handle(Message(text=case["question"]))
            latencies.append((time.perf_counter() - start) * 1000)
            good = is_correct(case, response)
            correct += good
            if case.get("expect_abstain"):
                abstain_total += 1
                abstain_ok += good
            if not good:
                failures.append(case["id"])
        rows.append(
            {
                "path": name,
                "correct": correct,
                "total": len(cases),
                "abstain_ok": abstain_ok,
                "abstain_total": abstain_total,
                "p50_ms": statistics.median(latencies),
                "max_ms": max(latencies),
                "failures": failures,
            }
        )
    return rows


def main() -> int:
    settings = load_settings()
    rows = run(settings, load_cases())
    print(f"{'path':18} {'correct':>8} {'abstain ok':>11} {'p50 ms':>8} {'max ms':>8}")
    for r in rows:
        print(
            f"{r['path']:18} {r['correct']:>5}/{r['total']} {r['abstain_ok']:>7}/{r['abstain_total']}"
            f" {r['p50_ms']:8.2f} {r['max_ms']:8.2f}   fails: {' '.join(r['failures']) or '-'}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
