# Hùng — Part E / A1: implementation and test evidence

Date: 2026-11-14. Branch: `feat/lab06-abstain-a1`.

This is module-level evidence and an integration handoff. The official three-path
comparison on the shared 25 cases is still pending; this document does not claim
that the individual submission or the integrated Lab 06 release is complete.

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

## Remaining acceptance work

- Merge/reconcile the C/D dependency PRs, then rerun this branch without skips.
- Phát integrates service/CLI/API and runs regression; RAG remains disabled by default.
- Hương supplies 20+5 official cases; Khôi runs the three paths on the same set.
- Fill the actual comparison table, three observations and failure analysis here
  after those measurements exist. No latency/accuracy numbers are invented.
- Team lead confirms the teacher's individual A1–A2/comparison PR requirements.

The privacy guard is a small lexical heuristic: it cannot recognize every name,
paraphrase or language, and conservatively rejects standalone eight-digit IDs.
It is not authentication/authorization; private student records must not enter
the public KB. Source ID validation proves that a citation was retrieved, not
that every generated claim is semantically entailed by that source.
