# Lab 3 — Before/After Maintainability Review

- **Student:** Nguyễn Trần Minh Khang
- **GitHub username:** `kentlatoi`

## Scope

“Before” is `lab03/monolith/assistant_monolith.py`. “After” is the current
`assistant_core` package. `config.py`, `models.py`, `errors.py`, `tools.py`, and `router.py` are
implemented. `knowledge.py`, `responder.py`, `service.py`, `logging_setup.py`, and `__main__.py`
contain only placeholder docstrings; `__init__.py` contains only the package docstring. The
task refers to an integrated `load_handbook()`, but that function is absent locally and
`test_knowledge.py` is also a one-line placeholder. This snapshot therefore appears older or
incomplete compared with the described team version. All measurements below apply only to the
local files inspected here.

## Measurement Convention

A global is a name assigned directly at module level; imports, functions, classes, and class fields
are excluded. Bare handlers are only `except:` clauses without a type. Function length is the
inclusive AST span from `def` to `end_lineno`, including internal comments and blank lines. Ruff was
run on both versions with `assistant_core_lab/pyproject.toml`.

| Question | Before | After |
| --- | --- | --- |
| Where would you change the credit rate? How many places? | Change the single `RATE` global in the monolith. The retake multiplier is a separate global. | Use the single runtime setting `CREDIT_RATE_VND`; its source default is `Settings.credit_rate_vnd`. `tuition()` receives the rate as an argument and does not duplicate it. Service wiring is not implemented yet. |
| Can you run the tests without internet or an API key? | The manual `test()` needs no internet because `llm()` is simulated, but it sleeps and can fail randomly. It is not an assertion-based suite. | Yes. The default provider is `stub`, and the current deterministic suite passed **77 tests** locally without internet or an API key. Provider integration is not implemented. |
| What happens if `handbook.json` is missing? | `load()` catches the error with bare `except:`, prints `could not load handbook`, and continues with an empty handbook; rule questions then fall through. | In this local snapshot, nothing happens because no `load_handbook()` function exists. `DataError` is defined for missing or malformed knowledge data, but no local loader raises it. The behavior of the described integrated version cannot be verified here. |
| Is any secret printed or logged? | Yes. A hard-coded `API_KEY` is printed by `llm()` when `DEBUG` is true, together with part of the prompt. | Implemented modules do not print the key. `llm_api_key` comes from configuration and has `repr=False`. However, `logging_setup.py` is unfinished, so complete redaction behavior is not yet verified. |
| How long does it take a new teammate to find the fee logic? | Not timed. Fee parsing, validation, and calculation are mixed into the large `handle()` function. | Not timed. `tools.py`, `parse_credits()`, and `tuition()` make the fee logic easier to locate, while `router.py` contains intent selection. The unfinished service still needs explanation. |
| Number of global variables | **9**: `API_KEY`, `MODEL`, `RATE`, `RETAKE_RATE`, `DEBUG`, `history`, `offices`, `handbook`, and `BASE`. | **2** across the source package: `_ENVIRONMENT_FIELDS` and `GREETINGS`. |
| Number of bare `except:` blocks | **3**: two in `load()` and one in `main()`. | **0** across `src/assistant_core`. |
| Lines in the longest function | **56 lines**: `handle()` (lines 44–99). | **20 lines**: `load_settings()` (lines 43–62). In Minh Khang’s files, `_parse_labelled_credits()` is 16 lines and `route()` is 14. The package result also reflects unfinished modules. |
| `ruff check` issues | **8** using the package rules: `E401`, `I001`, three `E722`, `E711`, `BLE001`, and `E501`. | **0**; the final package check reported `All checks passed`. |
| Can you swap the LLM without touching the service? | No. `handle()` directly calls the module-level `llm()` function and uses global provider settings. | Not yet. `Settings.llm_provider` provides configuration groundwork, but `responder.py` and `service.py` are placeholders and no provider adapter exists. |

## Conclusion

**What improved most?** Tuition calculation and routing are now small, deterministic modules with explicit inputs, named errors, and focused tests.

**What became more complex?** The package has more files, shared models, configuration objects, and module boundaries that contributors must understand.

**What would I improve next?** I would first integrate or recover the team’s knowledge module, then complete provider abstraction, service composition, safe logging, and the CLI before claiming full replacement of the monolith.
