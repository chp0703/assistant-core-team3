# Lab 3 — Before/After Maintainability Review

- **Student:** Nguyễn Trần Minh Khang
- **GitHub username:** `kentlatoi`

## Scope

“Before” is `lab03/monolith/assistant_monolith.py`. “After” is the current integrated
`assistant_core` package. `config.py`, `models.py`, `errors.py`, `knowledge.py`, `tools.py`, and
`router.py` are implemented. `knowledge.py` validates the CSV and JSON data and provides office and
rule lookup. `responder.py`, `service.py`, `logging_setup.py`, and `__main__.py` are one-line
placeholders; `__init__.py` contains only a package docstring. The package is therefore not yet a
complete end-to-end service.

## Measurement Convention

A global is a name assigned directly at module level; imports, functions, classes, and class fields
are excluded. A bare handler is `except:` without a type. Function length is the inclusive AST span
from `def` to `end_lineno`. Ruff used `assistant_core_lab/pyproject.toml`; the package and monolith
were checked separately with the same rules.

| Question | Before | After |
| --- | --- | --- |
| Where would you change the credit rate? How many places? | Change the single `RATE` global; the retake multiplier is separate. | Change `CREDIT_RATE_VND`; its default is `Settings.credit_rate_vnd`. `tuition()` receives the rate, so the formula does not duplicate it. Service wiring is pending. |
| Can you run the tests without internet or an API key? | The manual `test()` needs no internet because `llm()` is simulated, but it sleeps, can fail randomly, and has no assertions. | Yes. The default provider is `stub`. The integrated suite passed **80 tests** locally without either resource. The earlier H1 verification was **77 passed**. |
| What happens if `handbook.json` is missing? | `load()` catches the failure with bare `except:`, prints `could not load handbook`, and continues with an empty handbook. | `load_handbook()` catches `OSError` and raises `assistant_core.knowledge.KnowledgeError` with the path and original error. A direct missing-file check confirmed this behavior; `test_knowledge.py` covers missing offices and a malformed handbook, but not this exact branch. |
| Is any secret printed or logged? | Yes. With `DEBUG = True`, `llm()` prints the hard-coded `API_KEY` and part of the prompt. | Implemented modules do not print the key. `llm_api_key` comes from configuration and has `repr=False`. However, `logging_setup.py` is still a placeholder, so a complete logging and redaction policy is not implemented. |
| How long does it take a new teammate to find the fee logic? | Not timed. Parsing, validation, and calculation are mixed into the 56-line `handle()`. | Not timed. `tools.py` contains `parse_credits()` and `tuition()`, while `router.py` selects the intent. Easier discovery is a qualitative judgment. |
| Number of global variables | **9**: `API_KEY`, `MODEL`, `RATE`, `RETAKE_RATE`, `DEBUG`, `history`, `offices`, `handbook`, and `BASE`. | **2** across `src/assistant_core`: `_ENVIRONMENT_FIELDS` and `GREETINGS`. |
| Number of bare `except:` blocks | **3**: two in `load()` and one in `main()`. | **0** across `src/assistant_core`; loaders catch named exceptions. |
| Lines in the longest function | **56 lines**: `handle()` (lines 44–99). | **20 lines**, shared by `load_settings()` (43–62), `load_offices()` (70–89), and `load_handbook()` (92–111). |
| `ruff check` issues | **8** with the package rules: `E401`, `I001`, three `E722`, `E711`, `BLE001`, and `E501`. | **0** in the current integrated project; Ruff reported `All checks passed!`. |
| Can you swap the LLM without touching the service? | No. `handle()` directly calls the module-level `llm()` and uses global provider settings. | Not yet. `Settings.llm_provider` provides configuration groundwork, but no provider adapter exists and `responder.py` and `service.py` remain placeholders. |

## Conclusion

**What improved most?** Tuition, routing, configuration, and knowledge loading are separated into small modules with explicit inputs, named errors, and deterministic tests.

**What became more complex?** The package has more interfaces, data classes, configuration fields, and module boundaries for contributors to understand.

**What would I improve next?** I would connect the implemented router, tools, and knowledge layer through the service, add the responder and provider adapter, complete safe logging and the CLI, and consider aligning `KnowledgeError` with the shared exception hierarchy.

