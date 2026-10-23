# Models and exceptions contract

Owner: Hiền (`AIVIETNAM-AIO-TheHien`). Based on tutorial Part B.2 and Steps 2 and 4.

## Public models

| Model | Contract |
| --- | --- |
| `Intent` | String enum: `greeting`, `fee`, `office`, `rule`, `unknown`. |
| `Message` | Required `text`: string, 1-2000 characters inclusive. `session_id`: string, default `local`. |
| `Source` | Required `id` and `title`, both strings. |
| `Response` | Required `answer` string and `intent` enum. `sources`: list of `Source`, default empty. `degraded`: boolean, default false. |

`Message` and `Response` keep the field names consumed by
`AssistantService.handle(Message) -> Response`. The models do not import the
service or other feature modules, avoiding circular dependencies.

Pydantic raises `ValidationError` for invalid model data, including empty or
overlong message text. Following the tutorial, text is preserved without
trimming; whitespace-only text satisfies the length constraint. Rejecting it
would be an additional behavior change for the team to agree on.

`Response.sources` uses `Field(default_factory=list)` to make independent lists
explicit. JSON serialization uses the enum's string values and nested source
objects, so future HTTP adapters can reuse the same contract.

## Named exceptions

All four domain-specific exceptions inherit from `AssistantError`:

| Exception | Owner and intended handling |
| --- | --- |
| `ConfigError` | Configuration loading: missing or invalid settings; report a startup error. |
| `DataError` | Knowledge loading: missing or malformed data; report a startup error. |
| `InvalidRequest` | Tools: a structurally valid message contains an unsupported request, such as out-of-range credits. |
| `ProviderError` | Responder: provider failure; the service should return a template fallback with sources and `degraded=True`. |

`ValidationError` stays separate from these domain exceptions. Existing
`AssistantError` and `ConfigError` imports remain compatible. Exceptions carry
the caller-provided message; callers should avoid putting credentials or full
user messages in it.

## Verification and integration

From `assistant_core_lab`, using the versions pinned in `requirements.txt`:

```sh
python -m pytest -q
python -m ruff check .
python -m ruff format --check src/assistant_core/models.py src/assistant_core/errors.py tests/test_models.py tests/test_errors.py
```

Model tests cover text boundaries, Unicode and session preservation, required
fields, all intent values, JSON round trips, nested source validation and source
list independence. Exception tests verify that callers can catch the common
base while retaining the specific failure type and message. Existing config
tests check compatibility with `ConfigError`.

Passing these checks verifies the currently implemented modules. End-to-end
service behavior and provider fallback still require the other team modules to
be integrated and tested.
