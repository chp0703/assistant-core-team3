# Lab 3 - Before / after maintainability comparison

Member: `chp0703`

| Question | Before | After |
|---|---|---|
| Where would you change the credit rate? How many places? | Change the global `RATE` constant in `lab03/monolith/assistant_monolith.py`; the normal rate is defined in one place, while the retake multiplier is a separate global. | Change `Settings.credit_rate_vnd` in `assistant_core/config.py` or set `CREDIT_RATE_VND`; the configuration value is defined in one place. The tuition calculation module is not implemented yet. |
| Can you run the tests without internet or an API key? | The monolith has only manual print-based checks. It uses a fake local `llm()` function, so it does not need internet, but it contains a hard-coded API key. | The configuration tests are designed to use `stub` and no API key. They could not run in this environment because `python-dotenv` is missing. |
| What happens if `handbook.json` is missing? | A bare `except:` prints `could not load handbook`; handbook requests then fall through to `Sorry I dont know`. | Handbook retrieval is not implemented in the current skeleton, so this behavior is not implemented or verified yet. |
| Is any secret printed or logged? | Yes. With `DEBUG = True`, `llm()` prints the hard-coded `API_KEY`. | `Settings.llm_api_key` uses `repr=False`; the current configuration module does not print or log it. No logging service exists yet. |
| How long does it take a new teammate to find the fee logic? | It is embedded in the large `handle()` function with routing, office lookup, handbook lookup, and LLM fallback. | Fee logic has not been implemented yet; the planned module boundary is `tools.py`. |
| Number of global variables | 9 module-level mutable/configuration values: API key, model, rates, debug flag, history, data stores, and base path. | One private environment-to-field mapping in `config.py`; runtime settings are grouped in the `Settings` model. |
| Number of bare `except:` blocks | 3. | 0 in the implemented configuration code; validation errors are caught specifically. |
| Lines in the longest function | `handle()` is about 58 lines and has several responsibilities. | `load_settings()` is about 24 lines and only loads and validates configuration. |
| `ruff check` issues | Not measured; Ruff is not installed in the current environment. | Not measured; Ruff is not installed in the current environment. |
| Can you swap the LLM without touching the service? | No. The model and API key are globals in the monolith. | Not yet end-to-end: `llm_provider` and `llm_api_key` provide configuration groundwork, but an LLM adapter/service has not been implemented. |

The largest improvement so far is configuration: credentials are no longer hard-coded in the new
package, numeric settings are validated, and a safe `stub` provider is the default. The project
has a clearer source/test layout, but the router, knowledge, tools, responder, and service
modules are still placeholders, so maintainability improvements for those responsibilities cannot
yet be claimed. I would next implement the remaining service components with focused tests and
then rerun the comparison, Ruff, and the full test suite in an environment with the pinned
dependencies installed.
