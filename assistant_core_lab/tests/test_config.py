from pathlib import Path

import pytest

from assistant_core.config import Settings, load_settings
from assistant_core.errors import ConfigError

ENVIRONMENT_NAMES = (
    "ASSISTANT_DATA_DIR",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LLM_TIMEOUT_S",
    "CREDIT_RATE_VND",
    "RETAKE_MULTIPLIER",
    "MAX_CREDITS",
    "LOG_LEVEL",
    "API_ADMIN_KEY",
    "WEATHER_URL",
    "WEATHER_TIMEOUT_S",
    "CAMPUS_LAT",
    "CAMPUS_LON",
    "RATE_LIMIT_PER_MIN",
    "DATABASE_URL",
    "SESSION_SALT",
    "RAG_ENABLED",
    "KB_DIR",
    "RETRIEVAL_KIND",
    "RETRIEVAL_MIN_SCORE",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "PROMPT_VERSION",
)


@pytest.fixture(autouse=True)
def clear_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SESSION_SALT", "test-session-salt")


def test_loads_default_settings() -> None:
    settings = load_settings(env_file=None)

    assert settings == Settings(session_salt="test-session-salt")


def test_loads_valid_environment_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_DATA_DIR", "custom-data")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("CREDIT_RATE_VND", "500000")
    monkeypatch.setenv("RETAKE_MULTIPLIER", "2.0")
    monkeypatch.setenv("MAX_CREDITS", "24")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = load_settings(env_file=None)

    assert settings.data_dir == Path("custom-data")
    assert settings.llm_provider == "local"
    assert settings.llm_api_key == "test-key"
    assert settings.credit_rate_vnd == 500_000
    assert settings.retake_multiplier == 2.0
    assert settings.max_credits == 24
    assert settings.log_level == "DEBUG"


def test_loads_values_from_dotenv_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=stub\nMAX_CREDITS=18\n", encoding="utf-8")

    settings = load_settings(str(env_file))

    assert settings.llm_provider == "stub"
    assert settings.max_credits == 18


def test_shell_environment_takes_precedence_over_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_PROVIDER=remote\nLLM_API_KEY=dotenv-key\n", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    settings = load_settings(str(env_file))

    assert settings.llm_provider == "stub"
    assert settings.llm_api_key == "dotenv-key"


def test_stub_provider_does_not_require_api_key() -> None:
    assert load_settings(env_file=None).llm_provider == "stub"


def test_missing_session_salt_is_not_replaced_with_a_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SALT")

    assert load_settings(env_file=None).session_salt is None


def test_non_stub_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "remote")

    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        load_settings(env_file=None)


@pytest.mark.parametrize(
    ("environment_name", "value"),
    (("CREDIT_RATE_VND", "invalid"), ("RETAKE_MULTIPLIER", "invalid"), ("MAX_CREDITS", "invalid")),
)
def test_invalid_numeric_configuration_raises_config_error(
    monkeypatch: pytest.MonkeyPatch, environment_name: str, value: str
) -> None:
    monkeypatch.setenv(environment_name, value)

    with pytest.raises(ConfigError, match="Invalid configuration"):
        load_settings(env_file=None)


def test_api_key_is_not_in_settings_representation() -> None:
    assert "secret-key" not in repr(Settings(llm_api_key="secret-key"))


def test_session_salt_is_not_in_settings_representation() -> None:
    assert "test-session-salt" not in repr(Settings(session_salt="test-session-salt"))


def test_lab6_defaults_and_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = load_settings(env_file=None)
    assert defaults.rag_enabled is False
    assert defaults.kb_dir == Path("data/kb")
    assert defaults.retrieval_kind == "bm25"
    assert defaults.retrieval_min_score == 2.0
    assert defaults.llm_model == "llama3.2"
    assert defaults.llm_base_url is None
    assert defaults.llm_timeout_s == 5.0
    assert defaults.prompt_version == "answer_v1"

    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("KB_DIR", "custom/kb")
    monkeypatch.setenv("RETRIEVAL_KIND", "hybrid")
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "3.5")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:3b")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_TIMEOUT_S", "12")
    monkeypatch.setenv("PROMPT_VERSION", "answer_v2")

    configured = load_settings(env_file=None)
    assert configured.rag_enabled is True
    assert configured.kb_dir == Path("custom/kb")
    assert configured.retrieval_kind == "hybrid"
    assert configured.retrieval_min_score == 3.5
    assert configured.llm_provider == "ollama"
    assert configured.llm_model == "qwen2.5:3b"
    assert configured.llm_base_url == "http://localhost:11434"
    assert configured.llm_timeout_s == 12.0
    assert configured.prompt_version == "answer_v2"


def test_kb_dir_follows_data_dir_and_normalizes_empty_optional_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_DATA_DIR", "alt-data")
    monkeypatch.setenv("LLM_API_KEY", "   ")
    monkeypatch.setenv("LLM_BASE_URL", "")

    settings = load_settings(env_file=None)
    assert settings.kb_dir == Path("alt-data/kb")
    assert settings.llm_api_key is None
    assert settings.llm_base_url is None


@pytest.mark.parametrize(
    ("environment_name", "value"),
    (
        ("RETRIEVAL_KIND", "dense"),
        ("RETRIEVAL_MIN_SCORE", "-0.5"),
        ("LLM_TIMEOUT_S", "0"),
        ("RAG_ENABLED", "maybe"),
    ),
)
def test_invalid_lab6_configuration_raises_config_error(
    monkeypatch: pytest.MonkeyPatch, environment_name: str, value: str
) -> None:
    monkeypatch.setenv(environment_name, value)

    with pytest.raises(ConfigError, match="Invalid configuration"):
        load_settings(env_file=None)
