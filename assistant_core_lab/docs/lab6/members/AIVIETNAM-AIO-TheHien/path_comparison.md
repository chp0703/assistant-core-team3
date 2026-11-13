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

## Three-path comparison: pending integration

| Path | Measured correct / total | Correct abstentions | p50 / max latency | Status |
| --- | --- | --- | --- | --- |
| Deterministic | Not measured | Not measured | Not measured | Comparison adapter pending |
| Retrieval | Not measured | Not measured | Not measured | Part C / Part E pending |
| LLM (stub) | Not measured | Not measured | Not measured | A2 unit-tested; full path pending |

`eval/compare_paths.py` is still a scaffold at this base. No comparison run or
failure list is claimed, and no example numbers from the PDF are reused.
After Part C, Part E, service integration and H1 merge, rerun the three paths on
the same 25 questions (20 original + 5 H1), then replace this table and write the
three observations from the actual results.

The PDF (page 18) requires each member's PR to include A1-A2 and a comparison
table. This Part D PR alone does not establish that the individual submission
requirement is met. The team lead must confirm whether evidence from the shared
implementation is sufficient or each branch needs its own implementation.
S1-S3 practice evidence is also not established by this Part D change.

## H2 reflection draft (five lines)

1. RAG is like an open-book exam: the assistant first finds a relevant passage in our documents.
2. It gives that passage and the question to the language model to phrase an answer.
3. Our code checks the JSON shape and whether cited IDs belong to the retrieved passages.
4. When search finds no adequate evidence, A1 should stop before the model and suggest human support.
5. A valid citation alone cannot prove every sentence is true, so checking failures still matters.
