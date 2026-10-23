# Models and exceptions contract

Owner: Hiển (`AIVIETNAM-AIO-TheHien`). Based on tutorial Part B.2 and Steps 2 and 4.

## Public models

| Model | Contract |
| --- | --- |
| `Intent` | String enum: `greeting`, `fee`, `office`, `rule`, `unknown`. |
| `Message` | Required `text`: string, stripped at both ends, then checked for 1-2000 characters inclusive. `session_id`: string, default `local`. |
| `Source` | Required `id` and `title`, both strings. |
| `Response` | Required `answer` string and `intent` enum. `sources`: list of `Source`, default empty. `degraded`: boolean, default false. |

`Message` and `Response` keep the field names consumed by
`AssistantService.handle(Message) -> Response`. The models do not import the
service or other feature modules, avoiding circular dependencies.

Pydantic raises `ValidationError` for invalid model data, including empty,
whitespace-only or overlong normalized message text. The H1 extension uses
field-scoped `StringConstraints` to strip leading/trailing whitespace before
checking length. Unicode and internal whitespace are retained. `session_id`,
source references and response text are unchanged.

This intentionally extends the initial tutorial contract: `Message(text="   ")`
now fails validation, while a 2000-character message padded with whitespace is
accepted after normalization. Standard Pydantic decoding and validation still
apply to byte input and invalid types. No router, service or provider change is
needed to use the model-level behavior.

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

Model tests cover normalized text boundaries, blank input, invalid types, UTF-8
bytes, Unicode and session preservation, required fields, all intent values,
JSON round trips, nested source validation and source list independence.
Exception tests verify that callers can catch the common
base while retaining the specific failure type and message. Existing config
tests check compatibility with `ConfigError`.

Passing these checks verifies the currently implemented modules. End-to-end
service behavior and provider fallback still require the other team modules to
be integrated and tested.
