import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str, cwd: Path = PROJECT_ROOT, **settings: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "ASSISTANT_DATA_DIR": str(PROJECT_ROOT / "data"),
        "LLM_PROVIDER": "stub",
        "LLM_API_KEY": "",
        "CREDIT_RATE_VND": "450000",
        "RETAKE_MULTIPLIER": "1.5",
        "MAX_CREDITS": "30",
        "LOG_LEVEL": "INFO",
        **settings,
    }
    return subprocess.run(
        [sys.executable, "-m", "assistant_core", *args],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )


def test_cli_tuition_separates_answer_and_json_log(tmp_path: Path) -> None:
    result = run_cli(
        "tuition",
        "for",
        "18",
        "credits",
        "and",
        "2",
        "retake",
        cwd=tmp_path,
        ASSISTANT_DATA_DIR=str(PROJECT_ROOT / "data"),
        LLM_API_KEY="secret-canary",
    )
    assert result.returncode == 0
    assert result.stdout == "Your tuition is 9,450,000 VND.\n"
    log = json.loads(result.stderr)
    assert log["intent"] == "fee" and log["degraded"] is False
    assert "secret-canary" not in result.stdout + result.stderr
    assert "tuition for 18" not in result.stderr


def test_cli_rule_displays_source() -> None:
    result = run_cli("can I register my thesis with 118 credits")
    assert result.returncode == 0
    assert "H26-5.3" in result.stdout and "120 accumulated credits" in result.stdout
    assert json.loads(result.stderr)["intent"] == "rule"


@pytest.mark.parametrize("text", ["", "  ", "x" * 2001])
def test_cli_invalid_input_has_no_traceback_or_input_echo(text: str) -> None:
    result = run_cli(text)
    assert result.returncode == 2 and result.stdout == ""
    assert "Invalid message" in result.stderr and "Traceback" not in result.stderr
    if text.strip():
        assert text not in result.stderr


@pytest.mark.parametrize(
    "settings",
    [
        {"ASSISTANT_DATA_DIR": "does-not-exist"},
        {"MAX_CREDITS": "invalid"},
        {"LLM_PROVIDER": "remote"},
        {"LLM_PROVIDER": "remote", "LLM_API_KEY": "secret-canary"},
        {"LOG_LEVEL": "not-a-level"},
    ],
)
def test_cli_startup_failure_is_controlled(settings: dict[str, str]) -> None:
    result = run_cli("hi", **settings)
    assert result.returncode == 1 and result.stdout == ""
    assert "Cannot start assistant:" in result.stderr
    assert "Traceback" not in result.stderr and "secret-canary" not in result.stderr


def test_cli_requires_message() -> None:
    result = run_cli()
    assert result.returncode == 2 and "usage:" in result.stderr


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("hi", "greeting"),
        ("fee 18 credits and 2 retake", "fee"),
        ("thesis registration credits", "rule"),
        ("xyzzy qqqq", "unknown"),
    ],
)
def test_cli_json_is_a_structured_response(text: str, intent: str) -> None:
    from assistant_core.models import Response

    result = run_cli("--json", text)
    assert result.returncode == 0
    response = Response.model_validate_json(result.stdout)
    assert response.intent.value == intent
    assert set(json.loads(result.stdout)) == {"answer", "intent", "sources", "degraded"}
    assert bool(response.sources) is (intent == "rule")
    assert not response.degraded
    assert json.loads(result.stderr)["intent"] == intent


def test_cli_json_with_invalid_input_does_not_emit_partial_json() -> None:
    result = run_cli("--json", "   ")
    assert result.returncode == 2 and result.stdout == ""
    assert "Invalid message" in result.stderr


def test_cli_json_does_not_expose_settings_or_question() -> None:
    question = "xyzzy private-question-canary"
    result = run_cli("--json", question, LLM_API_KEY="private-key-canary")
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "private-key-canary" not in combined and question not in combined
    assert "llm_api_key" not in combined


def test_cli_json_supports_vietnamese_input() -> None:
    result = run_cli("--json", "học phí 18 tín chỉ và 2 tín chỉ học lại")
    assert result.returncode == 0
    assert json.loads(result.stdout)["answer"] == "Your tuition is 9,450,000 VND."


@pytest.mark.parametrize("handbook", [None, "{broken-json"])
def test_cli_missing_or_malformed_handbook_is_controlled(tmp_path: Path, handbook: str | None) -> None:
    (tmp_path / "offices.csv").write_text("name,room,hours\nLibrary,B.201,Mon-Sat\n", encoding="utf-8")
    if handbook is not None:
        (tmp_path / "handbook.json").write_text(handbook, encoding="utf-8")
    result = run_cli("--json", "hi", ASSISTANT_DATA_DIR=str(tmp_path))
    assert result.returncode == 1 and result.stdout == ""
    assert "Cannot start assistant:" in result.stderr
    assert "Traceback" not in result.stderr
