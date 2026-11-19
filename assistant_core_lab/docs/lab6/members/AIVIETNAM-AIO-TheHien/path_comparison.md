# Mem2 - Part D / A2 evidence and integration handoff

Owner: Huynh Nguyen The Hien (`@AIVIETNAM-AIO-TheHien`).
Branch: `feat/lab06-grounding-a2`.
Base: `e487962` (`main`, including the foundation merged in PR #53).

## Implemented scope

- `LLM`, `AnswerDraft`, `build_prompt`, `parse_draft`, `StubLLM`, the instructor's
  optional Ollama/OpenAI-compatible adapters, and `make_llm` in `llm.py`.
- A2 rejects a non-abstaining draft if citations are missing or any cited ID is
  outside the retrieved `allowed_ids`. JSON/schema failures become `ProviderError`.
- The versioned prompt requests JSON only, answers from supplied sources, valid
  source IDs, and abstention when the supplied evidence is insufficient.
- Prompt rendering preserves literal placeholders in questions/source text.
  The offline stub reads only the source block and cannot cite a source forged
  in the question.
- HTTP failures, invalid provider payloads and empty content become safe
  `ProviderError` messages. All adapter tests use mock HTTP; no paid/live model
  inference was performed.
- Independent tests use structural hit doubles because Part C is still a scaffold
  at this base. Importing the LLM module does not require a runtime `Hit` import.

## Validation

Run from `assistant_core_lab/` using its existing virtual environment:

```powershell
$unitTemp = Join-Path $env:TEMP ("mem2-unit-" + [guid]::NewGuid().ToString())
.\.venv\Scripts\python.exe -m pytest -q tests/test_llm_grounding.py --basetemp=$unitTemp
.\.venv\Scripts\python.exe -m pytest -q tests/test_llm_grounding.py -k citation
$pytestTemp = Join-Path $env:TEMP ("mem2-pytest-" + [guid]::NewGuid().ToString())
.\.venv\Scripts\python.exe -m pytest -q --basetemp=$pytestTemp
.\.venv\Scripts\python.exe -m ruff check .
```

Results checked on 2026-11-13:

| Check | Observed result |
| --- | --- |
| Part D module tests | 73 passed |
| Citation-focused tests (`-k citation`) | 8 passed |
| Full project regression | 270 passed; one existing Starlette/AnyIO deprecation warning |
| Ruff | All checks passed |
| `git diff --check` | Passed |

The isolated temp directory avoids an existing Windows permission problem in
the machine's shared `pytest-of-joovn` directory; no application/test assertions
were changed to work around that environment problem.

## Handoff to Part E and service integration

The public signatures match the instructor starter:

```python
prompt = build_prompt(question, hits, version="answer_v1")
raw = llm.complete(prompt)
draft = parse_draft(raw, {hit.chunk.id for hit in hits})
```

Part E must make the A1 decision before calling the model, handle model abstention,
catch `ProviderError`, retry once, and fall back to retrieved text if still invalid.
It must construct the shared internal `RagResult`, rather than modifying public
`Response`. For mock failures it can use `StubLLM(fail=True)` or
`StubLLM(garbage=True)`. HTTP adapter owners can call `close()` when disposing of
their clients.

`parse_draft` accepts one JSON object, including surrounding whitespace, and
rejects Markdown fences or prose surrounding JSON. This deliberately follows the
prompt's JSON-only requirement; the reference's permissive regex extraction was
not retained.

A2 checks citation membership, not whether every assertion is semantically
supported by that citation. Model confidence is not a calibrated probability.
The prompt's 80-word instruction is not a semantic correctness guarantee.

## Three-path comparison (post-integration)

After Part C (#58), Part D (#56), Part E (#60), H1 (#55), Stage 3 service integration (#61),
and Part F (#63) merged into `main`, all three paths were measured on the shared 25 cases
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

1. Retrieval raises accuracy from `9/25` to `20/25` because the deterministic path only answers Fee, Office, and Greeting requests and abstains on every regulation question.
2. With the offline `StubLLM`, the LLM path matches retrieval (`20/25`) while `parse_draft` enforces strict JSON schema validation and A2 citation membership against retrieved IDs at sub-millisecond overhead.
3. All five remaining failures come from router precedence (`E13` tuition, `E15`/`E23` library) and BM25 lexical scoring (`E14` plural mismatch, `E19` exam chunk above threshold) rather than A2 grounding.

## H2 reflection (five lines)

1. RAG is like an open-book exam: the assistant first finds a relevant passage in our documents.
2. It gives that passage and the question to the language model to phrase an answer.
3. Our code checks the JSON shape and whether cited IDs belong to the retrieved passages.
4. When search finds no adequate evidence, A1 should stop before the model and suggest human support.
5. A valid citation alone cannot prove every sentence is true, so checking failures still matters.
