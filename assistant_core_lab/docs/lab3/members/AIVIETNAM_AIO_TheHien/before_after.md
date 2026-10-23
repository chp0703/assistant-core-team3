# Before / After Review - Hiển

- Member: `AIVIETNAM-AIO-TheHien`.
- Date: 2026-10-23.
- Assignment: shared models, named exceptions and their tests.
- Baseline: local `main` at `2999d51`; results include the H1 message-normalization extension documented here.
- Template: `lab03/worksheets/before_after_maintainability.md`.

## Scope of the comparison

Before means the supplied `lab03/monolith/assistant_monolith.py`. After means
the current `assistant_core_lab` working tree, including the configuration work
from the team and Hiển's models/errors work.

This snapshot is partially implemented: `service.py`, `router.py`, `tools.py`,
`knowledge.py`, `responder.py`, `logging_setup.py` and `__main__.py` are still
placeholders. Lower line counts and zero bare exceptions therefore do not prove
that the complete monolith behavior has been ported. The comparisons below
separate implemented behavior from the intended architecture.

## The ten worksheet questions

| Question | Before: supplied monolith | After: current local package |
| --- | --- | --- |
| Where would you change the credit rate? How many places? | Change the single `RATE` assignment in code; the fee branch reads it directly. | Set `CREDIT_RATE_VND` in the environment or `.env`; `load_settings()` reads it into `Settings.credit_rate_vnd`. Configuration tests pass, but tuition integration is still pending. |
| Can you run the tests without internet or an API key? | Yes: `llm()` is a simulated local function. However, it sleeps, fails randomly and the manual `test()` only prints results. | Yes: all 50 pytest cases run locally without a real API key. The 40 models/errors cases are deterministic; the other 10 check configuration. |
| What happens if `handbook.json` is missing? | `load()` catches the failure with bare `except:`, prints a message and continues. | `DataError` is defined, but the knowledge loader and startup service are not implemented here. A tested startup `DataError` cannot yet be claimed. |
| Is any secret printed or logged? | A hard-coded sample key is printed by `llm()` when `DEBUG` is true. | The implemented models/errors add no logging or credentials. Configuration hides the key from `repr`, with a passing test. End-to-end logging still needs implementation and testing. |
| How long does it take a new teammate to find the fee logic? | Not timed; it is embedded in `handle()`, together with unrelated behavior. | Not timed; the intended destination is `tools.py`, but that module is still a placeholder. No onboarding-time improvement is claimed as a measurement. |
| Number of global variables | 9 assigned module-level names, including 3 mutable containers: `history`, `offices`, `handbook`. | 1 assigned module-level name: the mutable `_ENVIRONMENT_FIELDS` dictionary in `config.py`. Models/errors contain no assigned module-level state. |
| Number of bare `except:` blocks | 3: two in `load()` and one in `main()`. | 0 across the current source package. This includes modules whose implementation is still pending. |
| Lines in the longest function | `handle()`: 56 lines. | `load_settings()`: 20 lines. The H1 extension uses field constraints rather than adding a custom normalization function. |
| `ruff check` issues | 8 with the package's configured rules: `E401` 1, `I001` 1, `E722` 3, `E711` 1, `BLE001` 1, `E501` 1. | 0 when run from `assistant_core_lab`, matching the CI working directory. |
| Can you swap the LLM without touching the service? | No adapter boundary: `handle()` calls the global `llm()` directly. | This is an architecture goal, not completed behavior in this snapshot: responder and service are placeholders. `ProviderError` and `Response.degraded` provide contracts for the future fallback path. |

## Measured size and test coverage

| Metric | Before | After |
| --- | --- | --- |
| Source Python files | 1 monolith | 11 files under `src/assistant_core`, including placeholders |
| Physical source lines, including comments and blank lines | 163 | 120 |
| Hiển's source lines | Not separated into modules | `models.py`: 29; `errors.py`: 21 |
| Automated model/error cases | No separate model/error pytest suite | 36 model cases + 4 exception cases = 40 |
| Entire package's passing pytest cases | The monolith has a print-based smoke function | 50: 40 models/errors + 10 configuration |
| H1 increment over the earlier refactor | Not applicable | 15 additional parametrized cases; one existing text-preservation test updated for the new contract |

Line spans were measured from Python AST `lineno` through `end_lineno`,
inclusive. Global counts include module-level assignments and constants, but
exclude imports, classes, functions and class fields. Mutable-container counts
refer to module-level list/dict/set literals. These definitions keep the counts
reproducible rather than copying the tutorial's approximate example numbers.

## What changed within the models/errors assignment

- Replaced magic input/error strings with validated `Message`, `Source` and
  `Response` contracts and the shared `Intent` enum.
- Added `DataError`, `InvalidRequest` and `ProviderError` under `AssistantError`,
  retaining the configuration module's existing exception imports.
- Made independent response source lists explicit with `default_factory=list`.
- Added boundary, nested-data, serialization and exception-hierarchy tests.
- Added H1 field-level normalization: trim `Message.text`, reject blank results,
  then enforce 1-2000 characters; preserve internal whitespace and other fields.
- Used `model_validate()` for raw test input and configured the nested source
  path for Pyright/Pylance import resolution.

## Verification

Run from `assistant_core_lab` with the pinned direct dependencies:

```sh
python -m pytest -q
python -m ruff check .
python -m ruff format --check src/assistant_core/models.py src/assistant_core/errors.py tests/test_models.py tests/test_errors.py
```

Observed results on 2026-10-23: **50 passed**, Ruff **0 issues**, formatting checks
**passed**. Pyright 1.1.414, using the root `pyrightconfig.json` and this project's
`.venv`, reported **0 errors and 0 warnings** on the four models/errors source
and test files. Ruff comparisons use the project working directory; an explicit
`--config` run from the repository root classifies imports differently and was
observed to report three `I001` issues, so it is not the invocation used here.

## Three-sentence conclusion

The largest verified improvement is a shared, validated model/error boundary
with deterministic tests, including the new message-normalization behavior.
The cost is more files, Pydantic concepts and an intentional change to how
surrounding whitespace is handled. Next, the team should implement and test the
remaining modules and fallback path before claiming complete behavioral
equivalence with the monolith.
