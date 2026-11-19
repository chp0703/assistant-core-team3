# Phạm Hùng Khôi — Stage 4: Part F path comparison

Owner: Phạm Hùng Khôi (`@phkhoiit-1508`). Branch: `feat/lab06-path-evaluation`.

The full report, with setup, failed cases and analysis, is in [`../../path_comparison.md`](../../path_comparison.md).

## Comparison table (25 cases, one run, StubLLM offline)

| Path | Correct / total | Correct abstentions | p50 latency | Max latency |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.05 ms | 0.75 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.10 ms | 0.27 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.57 ms | 1.37 ms |

## Verification

Run from `assistant_core_lab/` on 2026-11-16 (Python 3.14.8, `StubLLM`, no live API calls):

| Check | Observed result |
| --- | --- |
| `python eval/compare_paths.py` | Table above |
| `tests/test_compare_paths.py` | 3 passed |
| Full pytest suite | 356 passed |
| `ruff check .` | All checks passed |

## Recommendation (Three Sentences)

1. For handbook questions today, we would ship the **retrieval** path alongside deterministic Fee and Office tools, and only turn on a real LLM after measuring it on the same 25 cases.
2. Retrieval raises correctness from `9/25` to `20/25` in about `0.10 ms`, quotes verified source text directly, and avoids external model cost and hallucination risk.
3. The first failure we would fix is router keyword precedence on `E13`, `E15`, and `E23`, followed by plural normalization for `E14`.

## H2 — Reflection (5 Lines)

1. RAG works like an open-book exam: first the search index finds the relevant section of the handbook, and only then does the language model phrase an answer from that section.
2. Comparing all three paths on the same 25 questions shows that retrieval creates the main jump in coverage (`9/25` to `20/25`) while keeping latency under a millisecond.
3. When search returns no strong evidence, our code applies A1 abstention before calling the model so the assistant says it does not know instead of inventing rules.
4. Our code also checks structured JSON output and A2 citation membership — verifying every cited ID came from the retrieved hits, which the model cannot be trusted to enforce by itself.
5. Measuring failures systematically exposes router and ranking gaps (`E13`, `E14`, `E15`, `E19`, `E23`) that a model alone cannot fix.
