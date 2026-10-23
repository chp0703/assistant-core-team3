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
