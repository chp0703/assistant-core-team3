# Nguyễn Trần Minh Khang — Lab 06 Part C & Individual Path Comparison

## My Part — Part C

I am `@kentlatoi`. My assigned part was the knowledge base, chunking, and BM25 retrieval, merged in [PR #58](https://github.com/chp0703/assistant-core-team3/pull/58). I worked on [`chunker.py`](../../../../src/assistant_core/rag/chunker.py), [`index.py`](../../../../src/assistant_core/rag/index.py), and [`test_rag_retrieval.py`](../../../../tests/test_rag_retrieval.py). I did not implement the shared service, A1, or A2.

`chunker.py` reads the `---` front matter as key/value metadata, then splits each document at numbered `#` headings. The document ID and heading number form a stable source ID such as `H26#5.3`. The three Markdown knowledge-base files match the instructor's starter and produce 14 chunks; checked IDs include `F26#1`, `H26#5.3`, and `S26#3`.

The BM25 index tokenizes chunk titles and text, scores query word matches using `k1=1.5` and `b=0.75`, then returns positive-score hits in descending score order (ties use chunk ID). Its `Index.search(query, k) -> list[Hit]` contract lets the shared Part E answerer use these chunks. Retrieval itself makes no LLM call.

## Testing

At my Part C submission, the dedicated tests had **10 passed**, the then-current full project suite had **207 passed**, and Ruff reported **All checks passed**. These are historical submission results, not current suite counts. The thesis query ranked `H26#5.3` first. The [current retrieval tests](../../../../tests/test_rag_retrieval.py) check this, stable metadata, empty results, ordering, and tie handling.

For this report, I ran the evaluation below with the repository `.venv` on 2026-11-17 (Python 3.12.13, offline `StubLLM`, no live API). The local environment has no pytest or Ruff installed, so I inspected the [A1 answerer tests](../../../../tests/test_rag_answerer.py), [A2 grounding tests](../../../../tests/test_llm_grounding.py), and [service tests](../../../../tests/test_rag.py) but did not rerun them. Dependency download was unavailable.

## Path Comparison

The merged [Part F report](../../path_comparison.md) from [PR #63](https://github.com/chp0703/assistant-core-team3/pull/63) records this **shared 2026-11-16 run** on the same [25 cases](../../../../eval/cases.jsonl):

| Path | Correct / total | Correct abstentions | p50 | Max |
| --- | --- | --- | --- | --- |
| Deterministic | 9/25 | 7/7 | 0.05 ms | 0.75 ms |
| Retrieval | 20/25 | 6/7 | 0.10 ms | 0.27 ms |
| LLM (stub) | 20/25 | 6/7 | 0.57 ms | 1.37 ms |

My **new local run** of [`python eval/compare_paths.py`](../../../../eval/compare_paths.py) measured:

| Path | Correct / total | Correct abstentions | p50 | Max |
| --- | --- | --- | --- | --- |
| Deterministic | 9/25 | 7/7 | 0.01 ms | 0.55 ms |
| Retrieval | 20/25 | 6/7 | 0.02 ms | 0.04 ms |
| LLM (stub) | 20/25 | 6/7 | 0.05 ms | 0.47 ms |

Both runs use shared routing, so they measure more than my isolated index. Retrieval and LLM both failed E13 and E15/E23 because Fee and Office routing handled those questions. E14 ranked `H26#7.2` above expected `H26#6.1`. E19 matched an exam chunk above the abstention threshold when the case expected no answer.

## Observations and Conclusion

1. BM25 supplied source evidence and raised coverage over deterministic handling, but the router can prevent retrieval from running.
2. Matching words can rank a related chunk first, as in E14, or return evidence too weak for the actual question, as in E19. Changing the threshold may affect correct answers too.
3. The offline StubLLM did not improve accuracy over retrieval here. Shared A2 validates that cited IDs came from retrieved hits; it cannot prove every sentence is true.

The shared A1 [`RagAnswerer`](../../../../src/assistant_core/rag/answerer.py) abstains before generation for missing or low-score hits and blocks private requests before model use. Shared A2 [`parse_draft`](../../../../src/assistant_core/llm.py) validates structured output and rejects missing or unretrieved citations on non-abstaining answers. I learned that finding useful chunks is only one part of the pipeline; routing and evidence checks still need improvement. These 25 offline cases do not show how a live model would behave.
