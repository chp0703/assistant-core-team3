# Architecture

## Module responsibilities

- `assistant_core.config` loads and validates runtime configuration.
- `assistant_core.errors` defines assistant-specific exceptions.
- Future modules will provide the service interface, routing, knowledge access, and response generation.

TODO: Document those modules when later lab steps implement them.

## Service interface

The service interface has not been implemented in this project skeleton.

TODO: Define the supported request and response interface in a later lab step.

## Architecture decisions

- Source packages use a `src/` layout to keep imports explicit during development.
- Configuration is loaded from environment variables, with `.env` support for local development.
- The default LLM provider is `stub`, so local work does not require credentials.

TODO: Record decisions for service composition and external provider adapters as they are added.
