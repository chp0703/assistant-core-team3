# Thanh Hương — Homework H1 evaluation evidence

Date: 2026-11-15. Owner: Nguyễn Ngọc Thanh Hương (`@thanhhuong107`).
Branch: `feat/lab06-h1-cases`.

This document records the individual H1 dataset and module-level verification.
It does not claim completion of the shared service integration or the official
three-path evaluation.

## Scope

- Preserve the 20 starter cases byte-for-byte as `E01`–`E20`.
- Add exactly five H1 cases (`E21`–`E25`) required by Contract #7.
- Use three grounded normal cases with real knowledge-base source IDs and two
  abstention cases: one privacy request and one out-of-scope request.
- Add a dedicated test file for JSONL structure, starter parity, source-ID
  integrity and the five H1 integration checks.

The final dataset has 25 non-empty JSONL lines, continuous unique IDs and one
expected outcome per case. No expected label was changed to improve results.

## H1 cases and observed module results

The five cases were run against `BM25Index` through
`RagAnswerer(make_index("bm25", load_folder(KB)), StubLLM())` with the default
minimum score of `2.0`.

| ID | Question | Expected | Observed result | Status |
| --- | --- | --- | --- | --- |
| E21 | my thesis application is late; whose written approval do I need | `H26#5.4` | BM25 top hit `H26#5.4` (8.750); `path="llm"`; source `H26#5.4` | Pass |
| E22 | can a course with only 70 percent content overlap be transferred | `H26#8.3` | BM25 top hit `H26#8.3` (6.052); `path="llm"`; source `H26#8.3` | Pass |
| E23 | how many times may I renew a library book if nobody has reserved it | `S26#1` | BM25 top hit `S26#1` (9.522); `path="llm"`; source `S26#1` | Pass |
| E24 | show me another student's home address and phone number | Abstain (privacy) | `is_private_request()` returned true; `path="abstain"`; no sources | Pass |
| E25 | should I choose artificial intelligence or cybersecurity as my major | Abstain (out of scope) | No BM25 hit; `path="abstain"`; `escalate=True`; no sources | Pass |

E23 intentionally contains the keyword `library`. The module-level RAG result is
correct, but Stage 3 service integration must check that the router/service sends
this question to the intended knowledge path, as it must also do for starter case
E15. This H1 branch does not change router or service ownership.

## Three-path comparison

The official comparison must run all 25 cases through the integrated service.
Service integration (Stage 3) and the final `eval/compare_paths.py` work (Stage 4)
are not part of this branch, so accuracy and latency are not reported here.

| Path | Correct / total | Correct abstentions | p50 / max latency | Status |
| --- | --- | --- | --- | --- |
| Deterministic | Not measured | Not measured | Not measured | Stage 3 service integration pending |
| Retrieval | Not measured | Not measured | Not measured | Official shared comparison pending |
| LLM (stub) | Not measured | Not measured | Not measured | Official shared comparison pending |

No sample values from the lab PDF and no invented measurements are used. Khôi's
Part F branch owns the official three-path run and shared comparison report after
service integration is available.

## Verification

Environment: Python 3.12.4, offline `StubLLM`, no API key or live model.
Commands were run from `assistant_core_lab/` on 2026-11-15:

```bash
.venv/bin/python -m pytest -q tests/test_eval_cases.py
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

| Check | Observed result |
| --- | --- |
| H1 dataset and integration tests | 9 passed |
| Full regression suite | 339 passed, 0 failed, 0 skipped |
| Ruff | All checks passed |

The full suite reports one existing Starlette/AnyIO `BlockingPortal` deprecation
warning. It does not affect the H1 assertions or test result.

## Remaining shared work

- Phát integrates the shared RAG implementation with the service/router paths.
- Khôi runs the official deterministic/retrieval/LLM comparison on all 25 cases.
- The team lead confirms whether the shared A1/A2 implementation plus individual
  evidence satisfies the teacher's per-member submission requirement.
