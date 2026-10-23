# Before / After Review — khoi

This comparison focuses on the knowledge/data part of the Lab 03 refactor.

| Question | Before: monolith | After: refactored package |
|---|---|---|
| Where would you change the credit rate? How many places? | Change the global `RATE` in `assistant_monolith.py`; the value is coupled to the whole script. | Change `Settings.credit_rate_vnd` or `CREDIT_RATE_VND`; configuration is separate from knowledge loading. |
| Can you run the tests without internet or an API key? | There is no reliable automated test suite; the script may call the stub LLM path and uses a random timeout. | Yes. Knowledge loading/search tests are deterministic and local; the full test suite runs without internet or an API key. |
| What happens if `handbook.json` is missing? | A bare `except:` prints an error and the script continues with incomplete global state. | `load_handbook` raises `KnowledgeError` with the source path and loading error. |
| Is any secret printed or logged? | Yes. Debug output prints `API_KEY` when the fake LLM is called. | The knowledge layer has no secret and never prints credentials. |
| How long does it take a new teammate to find the fee logic? | Search the large `handle` function and the global `RATE`; routing and calculation are mixed. | Fee configuration is in `config.py`; knowledge concerns are isolated in `knowledge.py`. |
| Number of global variables | Several mutable globals: `history`, `offices`, `handbook`, and configuration constants. | The knowledge layer has no mutable module-level state; data is held by `KnowledgeBase`. |
| Number of bare `except:` blocks | Two. | Zero in the refactored knowledge module. |
| Lines in the longest function | `handle` is roughly 50 lines and handles many unrelated cases. | Knowledge loader/search functions are short and each has one responsibility. |
| `ruff check` issues | The monolith is not covered by the package CI checks. | 0 Ruff issues after import ordering was fixed. |
| Can you swap the LLM without touching the service? | No; the LLM call is embedded in the monolith. | Yes in principle; knowledge loading/search does not depend on an LLM, so provider changes stay outside this module. |

## Three-sentence reflection

The biggest improvement is the clear boundary around local knowledge sources, with validation and deterministic tests instead of shared globals and silent failures. The refactor is slightly more complex because it introduces domain types, an immutable knowledge object, and explicit error handling. I would still improve tokenization and ranking for punctuation, Vietnamese queries, and synonyms before using the search in a production service.
