# H1 — AI Extension Review: Safe JSON Logging

- Member: Hương (`thanhhuong107`).
- Feature: structured JSON logs for the assistant, with a safe allowlist of fields.
- Files: `src/assistant_core/logging_setup.py`, `src/assistant_core/responder.py`,
  `tests/test_logging_setup.py`, and `tests/test_responder.py`.

## 1. Prompt used

The repository does not contain a saved verbatim prompt or the raw first AI draft.
This is a summary reconstructed from the assigned responder/logging work, not an
exact quotation:

> Add a standard-library logging setup that emits one-line JSON to stderr. Include
> level, logger, and message, plus only approved context fields (`intent`,
> `latency_ms`, `session`, and `degraded`). Do not log arbitrary extras such as
> API keys or user questions. Make setup safe to call more than once, allow an
> injectable stream for tests, and add focused tests. Keep response generation
> behind a `Responder` protocol with deterministic template and stub adapters.

## 2. Code review and refinements

Because the raw first draft is not saved in the repository, the table records
the concrete review decisions visible in the checked-in implementation; it does
not claim to reproduce an unavailable draft word for word.

The central formatter behavior in the reviewed implementation is:

```python
for field in _SAFE_EXTRA_FIELDS:
    if hasattr(record, field):
        data[field] = getattr(record, field)
return json.dumps(data, ensure_ascii=False, default=str)
```

| # | AI-generated starting point | Problem found during review | Change in the reviewed code | Why |
|---|---|---|---|---|
| 1 | Include `LogRecord` extras in the JSON output. | Arbitrary extras could expose a question, API key, or unrelated private field. | Replaced open-ended extras with `_SAFE_EXTRA_FIELDS`; the regression test supplies `api_key` and `question` and checks they are absent. | The output has an explicit, testable data boundary. |
| 2 | Configure a new `StreamHandler` on every setup call. | Repeated initialization would duplicate each log line. | Reuse the marked handler and update its formatter/stream; a test calls setup twice and expects one handler. | Repeated setup remains predictable. |
| 3 | Write only to global stderr and retain the question for responder output. | Global stderr makes tests harder to isolate, while retaining the question is unnecessary for the deterministic adapters. | Allow an injected `TextIO`; discard the unused `question` in both adapters and use `ProviderError` for the simulated provider failure. | Tests can capture output directly and the adapter does not retain user text. |

## 3. Behavior checked

- A JSON record includes the standard fields and approved context fields.
- An `api_key` and a `question` passed as arbitrary extras are omitted.
- Calling `setup_logging()` twice leaves one handler.
- `TemplateResponder` and `StubLLMResponder` return deterministic responses; a
  simulated provider failure raises `ProviderError`.

No new dependency or external provider call is added by these modules. The
responder deliberately discards the original question instead of retaining or
logging it.

## 4. Tests and remaining review

- `python -m pytest -q tests/test_responder.py tests/test_logging_setup.py` —
  **5 passed**.
- Full package suite after integrating the latest team changes: `python -m pytest
  -q` — **85 passed**.
- Ruff could not be run locally because it is not installed in this environment.

Codex performed the technical review recorded here. Hương should personally
check that the reconstructed prompt and review decisions match the work she
intends to submit; this document does not claim that personal confirmation has
already happened.
