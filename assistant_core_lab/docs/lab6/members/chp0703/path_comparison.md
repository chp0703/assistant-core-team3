# Châu Hòa Phát — Lab 06 Integration & Individual Path Comparison

## My Part — Stage 0 Foundation & Stage 3 Service/CLI/API Integration

I am `@chp0703`. My assigned scope covered the shared RAG contract foundation in [PR #53](https://github.com/chp0703/assistant-core-team3/pull/53) and the Stage 3 unified service, CLI, and FastAPI integration in [PR #61](https://github.com/chp0703/assistant-core-team3/pull/61). I worked on [`rag/types.py`](../../../../src/assistant_core/rag/types.py), [`config.py`](../../../../src/assistant_core/config.py), [`service.py`](../../../../src/assistant_core/service.py), [`__main__.py`](../../../../src/assistant_core/__main__.py), [`test_rag.py`](../../../../tests/test_rag.py), [`test_service.py`](../../../../tests/test_service.py), [`test_cli.py`](../../../../tests/test_cli.py), and [`test_chat.py`](../../../../tests/api/test_chat.py). Part C retrieval, Part D LLM/A2 grounding, Part E A1 abstain/guard, Part F runner, and H1 evaluation cases were implemented by the assigned teammates on the same codebase.

[`service.py`](../../../../src/assistant_core/service.py) preserves `create_service(settings) -> AssistantService` and extends `AssistantService` with optional `rag: RagAnswerer | None = None`. When `RAG_ENABLED=false` (the default), Lab 03–05 behavior remains unchanged. When `RAG_ENABLED=true`, `create_service` loads chunks and the configured index (`bm25` by default), constructs the LLM adapter (`stub`, `template` for retrieval-only `llm=None`, `ollama`, or `openai`), enforces `is_private_request()` before routing, keeps deterministic `GREETING`, `FEE`, and `OFFICE` paths intact, routes regulation questions through `RagAnswerer.answer()`, and maps internal `RagResult` values onto the preserved public `Response` without modifying `ChatResponse`. `AssistantService.handle_with_rag_result()` exposes internal `RagResult` metadata cleanly for evaluation, while CLI ([`__main__.py`](../../../../src/assistant_core/__main__.py)) and FastAPI ([`main.py`](../../../../src/assistant_api/main.py)) share `load_settings()` → `create_service(settings)`.

## Testing

At Stage 0 ([PR #53](https://github.com/chp0703/assistant-core-team3/pull/53)), the suite had **197 passed** and Ruff passed. At Stage 3 ([PR #61](https://github.com/chp0703/assistant-core-team3/pull/61)), [`tests/test_rag.py`](../../../../tests/test_rag.py) had **10 passed**, the full suite reached **353 passed**, and Ruff passed (both historical submission snapshots).

For this updated individual evidence on `main` (`eb1e591`), I reran the checks from `assistant_core_lab/` on 2026-11-18 using the repository `.venv` (Python 3.12.2, `ruff 0.6.9`, offline `StubLLM`, no live API calls):

| Check | Observed result |
| --- | --- |
| `pytest -q tests/test_rag.py` | 10 passed |
| Full pytest regression (`pytest -q -ra`) | 356 passed, 0 failed, 0 skipped (1 existing Starlette/AnyIO `BlockingPortal` deprecation warning) |
| `ruff check .` | All checks passed |

## Path Comparison

The merged [Part F report](../../path_comparison.md) from [PR #63](https://github.com/chp0703/assistant-core-team3/pull/63) records this **shared 2026-11-16 run** on the same [25 cases](../../../../eval/cases.jsonl):

| Path | Correct / total | Correct abstentions | p50 | Max |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.05 ms | 0.75 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.10 ms | 0.27 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.57 ms | 1.37 ms |

My **new local run** of [`python eval/compare_paths.py`](../../../../eval/compare_paths.py) on `main` (`eb1e591`, 2026-11-18) measured:

| Path | Correct / total | Correct abstentions | p50 | Max |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.02 ms | 1.44 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.03 ms | 0.08 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.17 ms | 9.44 ms |

Failed cases match the shared Part F report across both runs:

- Deterministic: `E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23`
- Retrieval: `E13 E14 E15 E19 E23`
- LLM (stub): `E13 E14 E15 E19 E23`

All paths execute through the shared `AssistantService` routing pipeline, keeping Fee and Office rules intact per Contract #5 rather than adding ad-hoc hacks for `E13` (`tuition` routed to `FEE`) or `E15`/`E23` (`library` routed to `OFFICE`). `E14` reflects BM25 ranking `H26#7.2` above `H26#6.1`, and `E19` reflects BM25 scoring above `RETRIEVAL_MIN_SCORE=2.0` on a question requiring abstention.

## Observations and Conclusion

1. Integrating `RagAnswerer` behind `AssistantService` lifts accuracy from **9/25** (deterministic) to **20/25** while keeping deterministic Fee, Office, Greeting, SQLite persistence, CLI, and FastAPI `ChatResponse` contracts intact.
2. Enforcing `is_private_request()` before `route()` protects third-party student queries (`E18`, `E24`, and ID-bearing requests even when fee/office keywords appear), and keeping `RagResult` internal via `handle_with_rag_result()` avoids breaking Lab 03–05 response schemas.
3. Both Retrieval and `StubLLM` share the exact same 5 failures (`E13`, `E14`, `E15`, `E19`, `E23`) because routing precedence (`tuition`, `library`) and BM25 lexical ranking/threshold happen before LLM generation; `parse_draft` enforces citation grounding against retrieved hits, while live-model behavior and threshold calibration remain outside these 25 offline stub cases.

The shared A1 [`RagAnswerer`](../../../../src/assistant_core/rag/answerer.py) abstains before calling the model on missing/low-score evidence or private requests, and shared A2 [`parse_draft`](../../../../src/assistant_core/llm.py) rejects invalid schemas, missing citations, or unretrieved source IDs on non-abstaining drafts. Integrating RAG as a modular dependency behind `AssistantService` lets CLI and FastAPI share one configuration and fallback boundary safely.
