# Architecture

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `config.py` | Load environment / optional `.env` settings and validate numeric configuration. |
| `errors.py` | Define `AssistantError`, `ConfigError`, `DataError`, `InvalidRequest`, `ProviderError`. |
| `models.py` | Public Pydantic `Message`, `Response`, `Intent` and `Source` contract. |
| `router.py` | Choose greeting, fee, office or rule routing with deterministic rules. |
| `knowledge.py` | Load and validate office CSV and handbook JSON once; look up offices and rules. |
| `tools.py` | Parse credits and compute tuition without I/O or provider calls. |
| `responder.py` | `Responder` protocol, predictable offline stub and template fallback. |
| `service.py` | Compose dependencies and coordinate requests through `AssistantService.handle`. |
| `logging_setup.py` | Set up JSON logs on stderr using an allowlist of context fields. |
| `__main__.py` | Parse CLI arguments, initialize the service, print answers / sources, return exit codes. |

Dependencies flow from CLI to service to router / knowledge / tools / responder.
Shared types and exceptions do not import the service. Importing a module does
not read data, load `.env`, configure logging or call a provider.

## Service interface

```python
AssistantService(settings, offices, handbook, responder)
AssistantService.handle(msg: Message) -> Response
create_service(settings: Settings) -> AssistantService
```

- `Message`: `text` has 1-2000 characters and cannot be whitespace-only;
  `session_id` defaults to `local`. Construct a validated `Message` before calling the service.
- `Response`: `answer: str`, `intent: Intent`, `sources: list[Source]`,
  `degraded: bool = False`. `Source` contains the rule's `id` and `title`.
- Routing priority is greeting, fee, office, then rule search. If no rule or office
  matches, the response uses `Intent.UNKNOWN`, no sources and `degraded=False`.
- Invalid / missing credits return a helpful `Intent.FEE` response. This is a
  user input issue, not a provider fallback.
- A matched rule always supplies a source. A `ProviderError` switches to
  `TemplateResponder`, keeps that source and sets `degraded=True`.
- Invalid messages raise Pydantic `ValidationError` at the boundary. Bad
  configuration raises `ConfigError`; unreadable or malformed data raises
  `DataError` during startup. Unexpected programming errors are not silently swallowed.
- `create_service` loads knowledge once and composes the default stub. Only
  `LLM_PROVIDER=stub` is supported in Lab 3. Other provider names are rejected
  explicitly; real provider adapters belong to a later lab. Direct constructor
  injection remains available for testing other `Responder` implementations.

### CLI contract

Run from `assistant_core_lab`, after `pip install -r requirements.txt` and
`pip install -e .`:

```console
python -m assistant_core "tuition for 18 credits and 2 retake"
python -m assistant_core "can I register my thesis with 118 credits"
python -m assistant_core "hi" --session-id local-demo
```

The CLI accepts one message per invocation (quoted or split into words).
Answers and sources go to stdout; JSON logs and startup / validation errors
go to stderr. Exit codes: `0` for a handled request (including unknown questions
and invalid fee arguments), `1` for configuration / data startup errors, `2` for
invalid CLI arguments or message validation. No interactive REPL is implemented.

Relative `ASSISTANT_DATA_DIR` paths are relative to the working directory. Use an
absolute path when running elsewhere. `.env` is loaded from the working directory;
existing environment variables take precedence. Commit `.env.example`, never `.env`.

## Architecture decisions

1. **One orchestration entry point with dependency injection.** The CLI and future
   HTTP / UI adapters use `handle(Message) -> Response`; tests inject failing
   responders without network access or changes to the service.
2. **Fees use pure functions, not an LLM.** The same arguments give the same
   integer VND amount. Retake credits are additional to regular credits, preserving
   the reference calculation: `18 * 450000 + 2 * 450000 * 1.5 = 9450000`.
   Decimal arithmetic avoids binary float artefacts before truncation to whole VND.
3. **A provider protocol separates generation from orchestration.** The offline
   stub is deterministic and has an explicit failure switch. Provider errors use
   a knowledge-backed template fallback instead of crashing or inventing sources.
4. **Configuration is separate from code.** Settings come from the environment,
   support local `.env` files, and reject non-positive rates / limits and non-finite
   multipliers. Source uses the existing `src/` layout and pinned direct dependencies.
5. **Startup failures are explicit.** Invalid CSV / JSON, duplicate identifiers,
   empty datasets and missing files fail with `DataError` rather than producing a
   partially initialized service.
6. **Logs contain operational metadata.** Fixed messages record intent, latency,
   session ID and fallback status. The formatter excludes arbitrary extras and
   exception details; our call sites never log API keys, full questions or provider
   exception messages. Session IDs must be non-sensitive identifiers. CLI error
   output avoids Pydantic input dumps.

## Refactoring scope and verification

The Lab 3 target is greetings, office lookup, tuition, and handbook rules with
sources. The monolith's auxiliary `history`, `stats`, and `save` commands are not
part of this target and are not implemented in this service.

Intentional changes follow the tutorial: typed boundary errors replace magic
strings; fee formatting adds thousands separators; answers and sources are
structured; provider simulation is deterministic. Negative / fractional credits
and malformed datasets are explicitly rejected. Office matching uses full office
names as in the supplied reference; partial-name matching and `help` are not added.

Tests cover reference behavior, routing, model validation, bad data, configuration,
provider fallback, safe logging and CLI subprocess behavior. The characterisation
test compares against the provided `lab03/monolith/assistant_monolith.py` without
calling its random provider.

The supplied ZIP contained placeholders for every dependency except configuration
and base errors. Supporting modules were implemented to make Member 6 runnable;
reconcile them with teammates' newer implementations before integration. This
document describes the ZIP's implementation, not unseen remote branches.
