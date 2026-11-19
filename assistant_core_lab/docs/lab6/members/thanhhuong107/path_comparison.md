# Thanh Hương — Homework H1 evaluation evidence

Created: 2026-11-15. Comparison updated: 2026-11-17.
Owner: Nguyễn Ngọc Thanh Hương (`@thanhhuong107`).
Original H1 branch: `feat/lab06-h1-cases` (merged in PR #55).
Comparison update branch: `docs/lab06-thanhhuong107-path-comparison`.

This document records the individual H1 dataset, module-level verification and
the measured three-path comparison after the shared service integration and Part F
runner were merged.

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

E23 intentionally contains the keyword `library`. Its module-level RAG result is
correct, but the integrated router sends it to the deterministic Office path before
RAG, just like E15. This routing behavior explains why E23 fails in all three
integrated comparison paths; this H1 evidence update does not change router/service
ownership or the expected label.

## Three-path comparison

Measured on 2026-11-17 from `main` commit `eb1e591` with all 25 cases,
`RETRIEVAL_MIN_SCORE=2.0` and the offline `StubLLM`. Latency is from this single
run and will vary by machine; the correctness and failure lists match the shared
Part F report.

| Path | Correct / total | Correct abstentions | p50 latency | Max latency |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.01 ms | 0.20 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.01 ms | 0.03 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.09 ms | 0.77 ms |

Failed cases:

- Deterministic: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23
- Retrieval: E13 E14 E15 E19 E23
- LLM (stub): E13 E14 E15 E19 E23

The deterministic path correctly abstains on all seven abstention cases but cannot
answer most regulation questions. Retrieval raises correctness from 9/25 to 20/25;
the stub LLM keeps the same correctness because it answers from the same top BM25
hit. E13, E15 and E23 are routed to deterministic Fee/Office behavior before RAG;
E14 is a BM25 ranking miss; E19 retrieves exam-absence evidence above threshold
instead of abstaining. No expected label was changed to improve these results.

## Verification

Environment: Python 3.12.16 container, offline `StubLLM`, no API key or live model.
Commands were run from `assistant_core_lab/` on 2026-11-17:

```bash
python eval/compare_paths.py
python -m pytest -q tests/test_eval_cases.py
python -m pytest -q
python -m ruff check .
```

| Check | Observed result |
| --- | --- |
| H1 dataset and integration tests | 9 passed |
| Full regression suite | 356 passed, 0 failed, 0 skipped |
| Ruff | All checks passed |

The full suite reports one existing Starlette/AnyIO `BlockingPortal` deprecation
warning. It does not affect the H1 assertions or test result.

## Limits and handoff

- The dataset has 25 cases and uses a deterministic stub, so the results do not
  estimate real-model accuracy.
- The shared Part F report remains the canonical team comparison; this table is
  Thanh Hương's individual evidence using the same runner and cases.
- The team lead still needs to confirm whether shared A1/A2 implementation plus
  individual evidence satisfies the teacher's per-member submission requirement.
