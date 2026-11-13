"""Runtime configuration loading and validation."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from assistant_core.errors import ConfigError


class Settings(BaseModel):
    """Validated settings used by the assistant service."""

    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)
    llm_timeout_s: float = Field(default=5.0, gt=0)
    credit_rate_vnd: int = 450_000
    retake_multiplier: float = 1.5
    max_credits: int = 30
    log_level: str = "INFO"
    # Lab 4 — API
    api_admin_key: str | None = Field(default=None, repr=False)
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_s: float = Field(default=3.0, gt=0)
    campus_lat: float = 10.7626
    campus_lon: float = 106.6822
    rate_limit_per_min: int = Field(default=30, gt=0)
    # Lab 5 — persistence
    database_url: str = "sqlite:///assistant.db"
    session_salt: str | None = Field(default=None, repr=False)
    # Lab 6 — RAG & AI services contract
    rag_enabled: bool = False
    kb_dir: Path = Path("data/kb")
    retrieval_kind: Literal["bm25", "tfidf", "hybrid"] = "bm25"
    retrieval_min_score: float = Field(default=2.0, ge=0)
    llm_model: str = "llama3.2"
    llm_base_url: str | None = None
    prompt_version: str = "answer_v1"


_ENVIRONMENT_FIELDS = {
    "ASSISTANT_DATA_DIR": "data_dir",
    "LLM_PROVIDER": "llm_provider",
    "LLM_API_KEY": "llm_api_key",
    "LLM_TIMEOUT_S": "llm_timeout_s",
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
    "RAG_ENABLED": "rag_enabled",
    "KB_DIR": "kb_dir",
    "RETRIEVAL_KIND": "retrieval_kind",
    "RETRIEVAL_MIN_SCORE": "retrieval_min_score",
    "LLM_MODEL": "llm_model",
    "LLM_BASE_URL": "llm_base_url",
    "PROMPT_VERSION": "prompt_version",
}

_NULLABLE_STRING_FIELDS = frozenset({"llm_api_key", "llm_base_url", "api_admin_key", "session_salt"})
_KEYLESS_PROVIDERS = frozenset({"stub", "template", "ollama"})


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

    values: dict[str, object] = {}
    for environment_name, field_name in _ENVIRONMENT_FIELDS.items():
        value = os.getenv(environment_name)
        if value is None:
            continue
        if field_name in _NULLABLE_STRING_FIELDS:
            stripped = value.strip()
            values[field_name] = stripped or None
        else:
            values[field_name] = value

    if "kb_dir" not in values and "data_dir" in values:
        values["kb_dir"] = Path(str(values["data_dir"])) / "kb"

    try:
        settings = Settings(**values)
    except ValidationError as error:
        raise ConfigError(f"Invalid configuration: {_validation_message(error)}") from error

    if settings.llm_provider not in _KEYLESS_PROVIDERS and not settings.llm_api_key:
        raise ConfigError("LLM_API_KEY must be set when using an external LLM_PROVIDER.")
    return settings
