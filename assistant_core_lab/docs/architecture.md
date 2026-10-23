# Architecture

## Module responsibilities

- `assistant_core.config` loads and validates runtime configuration.
- `assistant_core.errors` defines assistant-specific exceptions.
- `assistant_core.responder` provides a replaceable response interface, deterministic template fallback, and predictable provider stub.
- `assistant_core.logging_setup` configures JSON logs on stderr with an allowlist of safe context fields.
- Other modules provide the service interface, routing, and knowledge access.

TODO: Document those modules when later lab steps implement them.

## Service interface

The service interface has not been implemented in this project skeleton.

TODO: Define the supported request and response interface in a later lab step.

## Architecture decisions

- Source packages use a `src/` layout to keep imports explicit during development.
- Configuration is loaded from environment variables, with `.env` support for local development.
- The default LLM provider is `stub`, so local work does not require credentials.
- Response generation stays behind the `Responder` protocol so providers can be swapped without changing the service.
- Logs use fixed event messages and approved context fields; they must not include API keys or full user questions.

TODO: Record decisions for service composition and external provider adapters as they are added.
