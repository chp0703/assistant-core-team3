"""Assistant-specific exception types."""


class AssistantError(Exception):
    """Base class for assistant-specific errors."""


class ConfigError(AssistantError):
    """Raised when configuration is missing or invalid."""


class DataError(AssistantError):
    """Raised when a knowledge file is missing or malformed."""


class InvalidRequest(AssistantError):
    """Raised when a valid message cannot be processed as requested."""


class ProviderError(AssistantError):
    """Raised when an AI provider fails to produce a usable answer."""
