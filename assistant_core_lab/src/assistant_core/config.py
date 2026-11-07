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
    api_admin_key: str | None = Field(default=None, repr=False)
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_s: float = Field(default=3.0, gt=0)
    campus_lat: float = 10.7626
    campus_lon: float = 106.6822
    rate_limit_per_min: int = Field(default=30, gt=0)
    database_url: str = "sqlite:///assistant.db"
    session_salt: str | None = Field(default=None, repr=False)


_ENVIRONMENT_FIELDS = {
    "ASSISTANT_DATA_DIR": "data_dir",
    "LLM_PROVIDER": "llm_provider",
    "LLM_API_KEY": "llm_api_key",
    "CREDIT_RATE_VND": "credit_rate_vnd",
    "RETAKE_MULTIPLIER": "retake_multiplier",
    "MAX_CREDITS": "max_credits",
    "LOG_LEVEL": "log_level",
    "API_ADMIN_KEY": "api_admin_key",
    "WEATHER_URL": "weather_url",
    "WEATHER_TIMEOUT_S": "weather_timeout_s",
    "CAMPUS_LAT": "campus_lat",
    "CAMPUS_LON": "campus_lon",
    "RATE_LIMIT_PER_MIN": "rate_limit_per_min",
    "DATABASE_URL": "database_url",
    "SESSION_SALT": "session_salt",
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
