# Lab 06 — Path comparison (Part F)

Owner: Phạm Hùng Khôi (`@phkhoiit-1508`). Branch: `feat/lab06-path-evaluation`.

## Setup

- Command, from `assistant_core_lab/`: `python eval/compare_paths.py` (runner in `eval/compare_paths.py`, test in `tests/test_compare_paths.py`).
- Cases: `eval/cases.jsonl`, 25 questions (18 with an expected source or text, 7 expected abstentions), identical for all three paths.
- Environment: Python 3.14.8, Windows, `StubLLM` offline, no live API calls, BM25 with `RETRIEVAL_MIN_SCORE=2.0`.
- All three paths use the same router, tools, knowledge base, index and threshold; only the regulation-question step differs.

| Path | What answers a regulation question |
| --- | --- |
| Deterministic | Nothing: Fee, Office and Greeting use rules/tools, every regulation question abstains |
| Retrieval | The best BM25 chunk, quoted with its source, no LLM |
| LLM (stub) | The same BM25 hits, then the stub LLM with structured output, grounding check and fallback |

A case counts as correct when: an expected abstention returns intent `unknown`; otherwise the answer contains `expect_contains`, or the sources include `expect_source`.

## Results

Measured in one run on 2026-11-16.

| Path | Correct / total | Correct abstentions | p50 latency | Max latency |
| --- | --- | --- | --- | --- |
| Deterministic | 9 / 25 | 7 / 7 | 0.05 ms | 0.75 ms |
| Retrieval | 20 / 25 | 6 / 7 | 0.10 ms | 0.27 ms |
| LLM (stub) | 20 / 25 | 6 / 7 | 0.57 ms | 1.37 ms |

Failed cases:

- Deterministic: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23
- Retrieval: E13 E14 E15 E19 E23
- LLM (stub): E13 E14 E15 E19 E23

Latency varies from run to run. In an earlier run the LLM path had a maximum of 13.85 ms against 1.37 ms here, so treat latency as an order of magnitude, not a ranking.

## Analysis

1. Retrieval is the step that answers regulation questions: it lifts the score from 9/25 to 20/25 at about 0.1 ms. The deterministic path's 7/7 abstentions are not a quality signal, because it abstains on every regulation question.
2. The LLM path scores the same as retrieval because the offline stub answers from the top retrieved chunk. The structured output and grounding check cost a few tenths of a millisecond here and add no accuracy. This run does not show what a real model would add or break.
3. The failures come from routing and ranking, not from the LLM:
   - E13, E15, E23: the router sends `tuition` to Fee ("How many credits?") and `library` to Office (library hours) before retrieval can answer. The expected sources are `F26#3` and `S26#1`.
   - E14: BM25 ranks `H26#7.2` (exam absence) above `H26#6.1` (credit limit).
   - E19: the only wrong abstention result. "Is the final exam open-book" matches `H26#7.2` above the threshold and gets an answer instead of an abstention.

## Limits

- 25 cases and a stub LLM, so the accuracy numbers do not say how a real model behaves.
- Labels were not changed to improve results.
- Raising `RETRIEVAL_MIN_SCORE` could fix E19 but may break correct retrievals; it was not tuned here.
