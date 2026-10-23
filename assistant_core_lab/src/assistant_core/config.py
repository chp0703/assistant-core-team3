"""Runtime configuration loading and validation."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from assistant_core.errors import ConfigError


class Settings(BaseModel):
    """Validated settings used by the assistant service."""

    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)
    credit_rate_vnd: int = 450_000
    retake_multiplier: float = 1.5
    max_credits: int = 30
    log_level: str = "INFO"


_ENVIRONMENT_FIELDS = {
    "ASSISTANT_DATA_DIR": "data_dir",
    "LLM_PROVIDER": "llm_provider",
    "LLM_API_KEY": "llm_api_key",
    "CREDIT_RATE_VND": "credit_rate_vnd",
    "RETAKE_MULTIPLIER": "retake_multiplier",
    "MAX_CREDITS": "max_credits",
    "LOG_LEVEL": "log_level",
}


def _validation_message(error: ValidationError) -> str:
    details = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        details.append(f"{location}: {item['msg']}")
    return "; ".join(details)


def load_settings(env_file: str | None = ".env") -> Settings:
    """Load settings from the environment and optionally a dotenv file."""
    if env_file is not None:
        load_dotenv(env_file, override=False)

    values = {
        field_name: value
        for environment_name, field_name in _ENVIRONMENT_FIELDS.items()
        if (value := os.getenv(environment_name)) is not None
    }

    try:
        settings = Settings(**values)
    except ValidationError as error:
        raise ConfigError(f"Invalid configuration: {_validation_message(error)}") from error

    if settings.llm_provider != "stub" and not (settings.llm_api_key and settings.llm_api_key.strip()):
        raise ConfigError("LLM_API_KEY must be set when LLM_PROVIDER is not 'stub'.")

    return settings
