# AI Extension Review — khoi

## Feature and prompt

I asked the AI coding assistant:

> Extend the Lab 03 knowledge layer with deterministic handbook-rule search. Load `offices.csv` and `handbook.json` from the configured data directory, validate malformed input with a domain-specific exception, and add tests for office lookup, rule ranking, missing files, and malformed JSON. Do not add an external API or print secrets.

The feature was implemented in `src/assistant_core/knowledge.py` with tests in `tests/test_knowledge.py`.

## Manual review

| # | What the AI generated | Problem found | What I changed | Why |
|---|---|---|---|---|
| 1 | A knowledge module that loads the CSV and JSON files. | File parsing errors could otherwise leak low-level exceptions. | Added `KnowledgeError` and validation for required columns, empty fields, JSON shape, and rule fields. | Callers receive one clear domain-level failure mode. |
| 2 | A keyword search that returns matching handbook rules. | A test initially assumed only two rules could match a query containing `credits`; other credit-related rules are valid matches. | Kept all positive matches ranked by score and changed the test to verify the two most relevant results. | The test checks ranking without rejecting valid matches. |
| 3 | Mutable lists exposed from the knowledge object. | Callers could accidentally alter shared loaded knowledge. | Stored offices and rules as tuples in frozen dataclasses. | The loaded knowledge view is stable after construction. |

## Review checklist

- Interfaces: independent of routing, response generation, and LLM providers.
- Dependencies: no new dependency added.
- Secrets: no API key is loaded, printed, or logged by this module.
- User data: only local reference data is read.
- Tests: loading, office lookup, ranking, missing CSV, and malformed JSON are covered.
- Verification: Ruff passes and pytest reports 13 passing tests.
