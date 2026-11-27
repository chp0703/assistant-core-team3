"""Lab 08 H1: verify the public setup_logging behavior with isolated streams."""

import json
import logging
import sys
from collections.abc import Iterator
from io import StringIO

import pytest

from assistant_core.logging_setup import setup_logging


@pytest.fixture
def isolated_logger(monkeypatch: pytest.MonkeyPatch) -> Iterator[logging.Logger]:
    logger = logging.getLogger("assistant_core")
    original_level = logger.level
    monkeypatch.setattr(logger, "handlers", [])
    monkeypatch.setattr(logger, "propagate", logger.propagate)
    try:
        yield logger
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(original_level)


def test_default_setup_uses_stderr_at_info_level(
    isolated_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    stderr = StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)

    logger = setup_logging()
    logger.debug("filtered")
    logger.info("ready")

    assert logger is isolated_logger
    assert logger.level == logging.INFO
    assert not logger.propagate
    assert len(stderr.getvalue().splitlines()) == 1
    assert json.loads(stderr.getvalue()) == {"level": "INFO", "logger": "assistant_core", "msg": "ready"}


def test_reconfiguration_moves_output_and_updates_threshold(isolated_logger: logging.Logger) -> None:
    first = StringIO()
    second = StringIO()
    logger = setup_logging("WARNING", stream=first)
    logger.info("filtered")
    logger.warning("first")

    assert setup_logging("debug", stream=second) is isolated_logger
    logger.debug("second")

    assert len(logger.handlers) == 1
    assert json.loads(first.getvalue())["msg"] == "first"
    assert json.loads(second.getvalue())["msg"] == "second"


@pytest.mark.parametrize("latency_ms", [0, 10**30], ids=["zero", "very-large"])
def test_numeric_context_survives_json_round_trip(isolated_logger: logging.Logger, latency_ms: int) -> None:
    stream = StringIO()
    logger = setup_logging(stream=stream)
    logger.info("handled", extra={"latency_ms": latency_ms})

    value = json.loads(stream.getvalue())["latency_ms"]
    assert type(value) is int
    assert value == latency_ms


def test_vietnamese_message_survives_json_round_trip(isolated_logger: logging.Logger) -> None:
    stream = StringIO()
    logger = setup_logging(stream=stream)
    message = "Đã xử lý yêu cầu học phí."

    logger.info(message)

    assert message in stream.getvalue()
    assert json.loads(stream.getvalue())["msg"] == message


def test_empty_level_is_rejected(isolated_logger: logging.Logger) -> None:
    with pytest.raises(ValueError, match="Unknown level"):
        setup_logging("", stream=StringIO())

    assert isolated_logger.handlers == []


def test_non_string_level_is_rejected(isolated_logger: logging.Logger) -> None:
    with pytest.raises(AttributeError, match="upper"):
        setup_logging(12, stream=StringIO())  # type: ignore[arg-type]

    assert isolated_logger.handlers == []
