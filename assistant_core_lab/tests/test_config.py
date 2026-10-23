from pathlib import Path

import pytest

from assistant_core.config import Settings, load_settings
from assistant_core.errors import ConfigError

ENVIRONMENT_NAMES = (
    "ASSISTANT_DATA_DIR",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "CREDIT_RATE_VND",
    "RETAKE_MULTIPLIER",
    "MAX_CREDITS",
    "LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def clear_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_loads_default_settings() -> None:
    settings = load_settings(env_file=None)

    assert settings == Settings()


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
