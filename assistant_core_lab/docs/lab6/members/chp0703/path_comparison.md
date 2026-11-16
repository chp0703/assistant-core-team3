# Châu Hòa Phát — Stage 3: Service, CLI & API RAG Integration

Owner: Châu Hòa Phát (`@chp0703`).  
Branch: `feat/lab06-unify-service` (branched from `main` at `c74bfa4`).

This document records Stage 3 unified service integration (`Contract #5`) and serves as the handoff to Stage 4 (`Contract #6 — Part F` owned by `@phkhoiit-1508`).

## Scope Implemented

- `src/assistant_core/service.py`:
  - Preserved `create_service(settings: Settings) -> AssistantService` (did not rename to `build_service()`).
  - Added optional `rag: RagAnswerer | None = None` to `AssistantService.__init__`, keeping Lab 03–05 behavior intact whenever `rag is None` (`RAG_ENABLED=false`, default).
  - Wired `create_service(settings)` when `rag_enabled=True` using `load_folder(kb_dir)` + `make_index(settings.retrieval_kind, chunks)` + `_build_rag_llm(settings)` (`stub`, `template` as retrieval-only `llm=None`, `ollama`, `openai`) + `RagAnswerer(..., min_score=settings.retrieval_min_score, prompt_version=settings.prompt_version)`.
  - Added `AssistantService.handle_with_rag_result(msg)` so internal evaluation can inspect `(Response, RagResult | None)` without adding `path`, `escalate`, or `confidence` to the public `Response` or HTTP `ChatResponse` schema.
  - Applied `is_private_request()` before `route()` (Greeting, Fee, Office, Retrieval/LLM) whenever RAG is enabled, while preserving existing deterministic rules/tools for `GREETING`, `FEE`, and `OFFICE`.
  - Converted startup failures (`missing/empty kb_dir`, invalid `LLM_PROVIDER`, missing `LLM_API_KEY`) to fail fast with `DataError` or `ConfigError` without leaking secrets.
- `src/assistant_core/__main__.py`:
  - Caught `DataError` alongside `(ConfigError, KnowledgeError)` so CLI startup failures with `RAG_ENABLED=true` exit cleanly with code `1` and no traceback.
- Tests added/completed:
  - Replaced scaffold in `tests/test_rag.py` with 10 end-to-end integration tests covering `create_service`, `RAG_ENABLED=false/true`, deterministic routes preserved, privacy before fee/office/retrieval, `template`/`ollama`/`openai` settings forwarding, fail-fast startup validation, provider secret-safe fallback logging, and CLI + FastAPI shared-config parity with SQLite persistence.
  - Extended `tests/test_service.py`, `tests/test_cli.py`, and `tests/api/test_chat.py` for Stage 3 verification.

## Handoff to Stage 4 (Part F — Khôi `@phkhoiit-1508`)

- Both CLI (`assistant_core.__main__`) and FastAPI (`assistant_api.main.create_app`) construct `AssistantService` via `load_settings()` -> `create_service(settings)`.
- Public `Response` and HTTP `ChatResponse` intentionally omit `path`, `escalate`, and `confidence` per `Contract #5`.
- For `eval/compare_paths.py`, call `response, rag_result = service.handle_with_rag_result(Message(text=case["question"]))`:
  - When `rag_result is not None`, inspect `rag_result.path`, `rag_result.escalate`, `rag_result.confidence`, and `rag_result.degraded`.
  - When `rag_result is None`, the request took a deterministic route (`greeting`, `fee`, `office`, or Lab 03 handbook fallback).
- Routing observation on the 25-case `eval/cases.jsonl` preview (`RAG_ENABLED=true`, `LLM_PROVIDER=stub`): 20/25 pass with expected outcomes, and the 5 remaining cases (`E13`, `E14`, `E15`, `E19`, `E23`) reflect genuine Lab 06 router/BM25/stub limitations (`E13` matches `tuition` -> deterministic `FEE`; `E15`/`E23` match `library` -> deterministic `OFFICE`; `E14` BM25 ranks `H26#7.2` above `H26#6.1`; `E19` BM25 exceeds threshold `2.0`). Per `Contract #5` and `#7`, Greeting/Fee/Office rules were kept intact rather than bypassed with ad-hoc hacks so Part F can analyze authentic failure modes.

## Three-Path Comparison Status

Official 3-path comparison and latency measurements remain pending Stage 4 (`eval/compare_paths.py` owned by `@phkhoiit-1508`). No comparison numbers are invented here.

| Path | Correct / total | Correct abstentions | p50 / max latency | Status |
| --- | --- | --- | --- | --- |
| Deterministic | Not measured | Not measured | Not measured | Pending Stage 4 (`eval/compare_paths.py`) |
| Retrieval | Not measured | Not measured | Not measured | Pending Stage 4 (`eval/compare_paths.py`) |
| LLM (stub) | Not measured | Not measured | Not measured | Pending Stage 4 (`eval/compare_paths.py`) |

## Verification

Run from `assistant_core_lab/`:

```bash
.venv/Scripts/python -m pytest -q tests/test_rag.py
.venv/Scripts/python -m pytest -q
ruff check .
```

Verified on 2026-11-16 (`Python 3.12.2`, `ruff 0.6.9`, `StubLLM` offline, no live API calls):

| Check | Observed result |
| --- | --- |
| `tests/test_rag.py` | 10 passed |
| Full pytest suite | 353 passed, 0 failed, 0 skipped (1 existing Starlette/AnyIO `BlockingPortal` deprecation warning) |
| `ruff check .` | All checks passed |
