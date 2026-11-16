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
