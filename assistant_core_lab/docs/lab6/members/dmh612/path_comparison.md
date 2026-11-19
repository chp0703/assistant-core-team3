# Hùng — Part E / A1: implementation and test evidence

Date: 2026-11-14 (post-integration comparison & H2 updated 2026-11-19). Branch: `feat/lab06-abstain-a1` (merged in PR #60).

This document records Part E / A1 module-level evidence, integration handoff, and
the post-integration three-path comparison on the shared 25 cases.

## Scope

- `guard.py`: starter-compatible `is_private_request(text)` and `PRIVATE_REPLY`;
  English/Vietnamese third-party record patterns, Unicode/whitespace normalization.
- `rag/answerer.py`: shared `RagResult`, privacy before retrieval/model calls,
  A1 abstain for no hits or best score `< min_score`, retrieval-only mode,
  real Part D prompt/parser, one retry by default, safe source-preserving fallback.
- Optional starter-compatible `tool_runner(raw)` callback; no tool executes unless
  the application supplies a callback that validates tool names and arguments.
- Three dedicated test files; public Response, service/config, LLM, retrieval,
  tools and the official evaluation cases are unchanged.

Privacy refusal is `UNKNOWN`, `path="abstain"`, no sources, confidence `0.0`,
`escalate=False` (starter policy). Insufficient evidence and model abstention
escalate to the Training Office. A successful retry is not marked degraded;
exhausted provider/schema/grounding failures quote the original best chunk with
`degraded=True`. Model confidence is metadata, not measured answer accuracy.

## Verified results

Python 3.12.10, dependencies from `requirements.txt`, pytest 8.3.3, Ruff 0.6.9.
No live LLM, API key or model download was used.

| Verification target | Result |
| --- | --- |
| Main foundation + Hùng's changes: full pytest | 223 passed, 24 skipped |
| Pinned Part C + Part D + Hùng: own module/integration tests | 50 passed, no skips |
| Pinned Part C + Part D + Hùng: full pytest | 330 passed, no skips |
| Ruff, both source and combined validation copy | All checks passed |
| Whitespace diff and independent code review | No blocking findings |

Both full suites report one existing Starlette/AnyIO `BlockingPortal` deprecation
warning. Restricted execution stalled on the first FastAPI TestClient test;
the successful full suites ran with local connection access and separate pytest
temporary directories. No application code was changed to work around this.

The 24 skips are explicit checks for missing C/D dependencies on main, rather
than successful LLM/integration tests. They all ran and passed in the combined
copy using the real parser/index, not replacement production implementations.

Pinned revisions:

- Main foundation: `e487962882562f7070570fa0a1911435004ca696`.
- Part C, `feat/lab06-rag-knowledge-kent`: `145a78cadac506bbcde8fc292170b49e9f368af2`.
- Part D, `feat/lab06-grounding-a2`: `245abb67d4a26663520713d4d898a838276be115`.

In a disposable copy of this branch, the C/D snapshots supplied only:

```text
# Part C revision
assistant_core_lab/src/assistant_core/rag/chunker.py
assistant_core_lab/src/assistant_core/rag/index.py
assistant_core_lab/tests/test_rag_retrieval.py
# Part D revision
assistant_core_lab/src/assistant_core/llm.py
assistant_core_lab/src/assistant_core/prompts/answer_v1.txt
assistant_core_lab/tests/test_llm_grounding.py
```

Those snapshots are validation inputs only and are not included in Hùng's commit.
To reproduce, populate those six paths from their pinned revisions in a disposable
copy (for example `git restore --source=<revision> -- <paths>`), then run from
`assistant_core_lab/` with the project dependencies installed:

```bash
python -m pytest -q tests/test_privacy_guard.py tests/test_rag_answerer.py tests/test_rag_answerer_integration.py
python -m pytest -q -ra --basetemp <a-new-writable-temp-directory>
python -m ruff check .
```

Tests were written and observed failing before implementation: 26 failures for
missing guard/answerer functionality, then 22 expected failures for the unbuilt
LLM/retry/fallback paths in the combined copy. The final 50 own tests passed.
Coverage includes threshold equality, early privacy/abstain, original source text,
valid JSON/source mapping, missing/mixed/forged citations, invalid schema, provider
failure, recovery on retry, model abstention, unavailable prompt, safe logs and
the validated tool callback boundary.

## Handoff to Phát

After C/D merge, construct `RagAnswerer(index, llm, settings.retrieval_min_score,
prompt_version=settings.prompt_version)` inside the existing `create_service`.
For retrieval-only evaluation pass `llm=None`. Both CLI and API must continue to
use the same service. Map the internal result to the existing public contract:

```python
result = rag.answer(text)
response = Response(
    answer=result.answer,
    intent=result.intent,
    sources=list(result.sources),
    degraded=result.degraded,
)
```

Keep `path`, `escalate` and `confidence` internal for evaluation. Retain the guard
inside the answerer, and apply the service-level privacy check before any other
potentially sensitive route. Existing `tools.py` does not yet expose the starter's
`run_tool_call`; the optional callback needs a validated implementation before
enabling model-requested tools. Deterministic Fee handling stays in the service.

## Three-path comparison (post-integration)

After Part C (#58), Part D (#56), Part E (#60), H1 (#55), Stage 3 service integration (#61),
and Part F (#63) merged into `main`, all three paths were evaluated on the shared 25 cases
(`eval/cases.jsonl`, `RETRIEVAL_MIN_SCORE=2.0`, offline `StubLLM`).

Canonical Part F run ([`../../path_comparison.md`](../../path_comparison.md), 2026-11-16):

| Path | Correct / total | Correct abstentions | p50 latency | Max latency |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.05 ms | 0.75 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.10 ms | 0.27 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.57 ms | 1.37 ms |

Team release verification rerun on 2026-11-19 (`Python 3.12.2`, `StubLLM` offline, full suite `361 passed`, `ruff check .` pass):

| Path | Correct / total | Correct abstentions | p50 latency | Max latency |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.02 ms | 0.57 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.03 ms | 0.07 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.18 ms | 0.64 ms |

Failed cases:

- Deterministic: `E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23`
- Retrieval: `E13 E14 E15 E19 E23`
- LLM (stub): `E13 E14 E15 E19 E23`

Observations:

1. Privacy guard and A1 abstention correctly block `6/7` abstention cases (`E16`, `E17`, `E18`, `E20`, `E24`, `E25`) before any model generation; deterministic's `7/7` reflects abstaining on every regulation query.
2. Retrieval and `StubLLM` both lift overall accuracy from `9/25` to `20/25` because `RagAnswerer` grounds answers on the same top BM25 hits and falls back cleanly on provider errors.
3. The only abstention miss (`E19`) happens because BM25 scores an exam-absence chunk above `2.0`, while `E13`, `E15`, and `E23` are intercepted by deterministic Fee/Office routing and `E14` is a BM25 ranking miss.

## H2 — Reflection (5 Lines)

1. RAG acts like an open-book exam where the assistant searches official documents first and only then asks the model to explain the matching section.
2. Before the model is ever called, our code runs privacy guardrails and A1 abstention so sensitive or unsupported questions are refused immediately instead of guessed.
3. Giving the model retrieved chunks keeps its answer tied to current faculty rules rather than outdated training memory.
4. Unlike the language model itself, our code enforces strict JSON validation, checks via A2 that every cited ID came from the retrieved chunks, and retries once on failure.
5. If validation still fails or the provider is unavailable, `RagAnswerer` safely falls back to quoting the original retrieved chunk with `degraded=True`.

## Limits and notes

The privacy guard is a small lexical heuristic: it cannot recognize every name,
paraphrase or language, and conservatively rejects standalone eight-digit IDs.
It is not authentication/authorization; private student records must not enter
the public KB. Source ID validation proves that a citation was retrieved, not
that every generated claim is semantically entailed by that source.
