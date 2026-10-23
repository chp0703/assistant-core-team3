# Before / After Maintainability Review — Hương (`thanhhuong107`)

Comparison uses `lab03/monolith/assistant_monolith.py` and the package currently
in `assistant_core_lab/src/assistant_core`. Tuition tools and routing are now
implemented; `service.py` is still a placeholder, so end-to-end composition is
not assumed.

| Question | Before: monolith | After: package in this branch |
|---|---|---|
| Where would you change the credit rate? How many places? | Change `RATE` near the top of `assistant_monolith.py`; the fee formula reads that constant. | Change `Settings.credit_rate_vnd` in `config.py` or set `CREDIT_RATE_VND`; `tools.tuition()` receives the configured rate. The service composition is still pending. |
| Can you run the tests without internet or an API key? | There are only hand-run checks in the script. Its mock `llm()` makes no network request or API-key check, but can fail randomly. | Yes. The default provider is `stub`; tests use local data and test doubles, with no API key or internet required. |
| What happens if `handbook.json` is missing? | A bare `except` prints a generic message and leaves the global handbook empty; the process continues and later answers “Sorry I dont know”. | `load_handbook()` raises `KnowledgeError` with the path and cause. Startup handling is not wired yet because `service.py` is still a placeholder. |
| Is any secret printed or logged? | Yes. Debug output prints `API_KEY` and part of the prompt. | The config field is excluded from `repr`; JSON logging only includes an explicit safe-field allowlist and omits arbitrary fields such as `api_key` and `question`. |
| How long does it take a new teammate to find the fee logic? | Fee parsing and calculation are inside `handle()`, a 56-line function with several unrelated branches. | Fee parsing/calculation are grouped in `tools.py`, and rates are in `config.py`; the caller is not yet wired through `service.py`. |
| Number of global variables | 9 module-level values, including mutable `history`, `offices`, and `handbook`. | 4 module-level constants/config names; no mutable per-request global state. |
| Number of bare `except:` blocks | 3. | 0 in `assistant_core`. |
| Lines in the longest function | 56 (`handle`). | 23 (`setup_logging`). |
| `ruff check` issues | Not measured: Ruff is unavailable in this environment. | Not measured locally for the same reason; the repository CI runs Ruff on the package. |
| Can you swap the LLM without touching the service? | No. The `llm()` function is called directly from `handle()`. | A `Responder` protocol and template/stub adapters define the seam, but `service.py` is not wired yet, so a complete swap is not demonstrated. |

**Three sentences:** The biggest improvement is that configuration, knowledge,
tuition tools, routing, response generation, and logging now have separate,
testable boundaries, and logs no longer expose the key or question. The package
adds some complexity through settings, protocols, domain errors, and multiple
modules. I would finish service composition, add an end-to-end test for missing
handbook data and provider fallback, and run Ruff before calling the refactor
complete.
