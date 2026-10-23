"""Assistant-specific exception types."""


class AssistantError(Exception):
    """Base class for assistant-specific errors."""


class ConfigError(AssistantError):
    """Raised when configuration is missing or invalid."""
