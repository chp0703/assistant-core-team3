import json
import logging
from io import StringIO

from assistant_core.logging_setup import JsonFormatter, setup_logging


def test_json_formatter_includes_safe_fields_only() -> None:
    record = logging.LogRecord(
        name="assistant_core.service",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="handled",
        args=(),
        exc_info=None,
    )
    record.intent = "fee"
    record.latency_ms = 1.2
    record.session = "local"
    record.degraded = False
    record.api_key = "must-not-appear"
    record.question = "private user text"

    output = json.loads(JsonFormatter().format(record))

    assert output == {
        "level": "INFO",
        "logger": "assistant_core.service",
        "msg": "handled",
        "intent": "fee",
        "latency_ms": 1.2,
        "session": "local",
        "degraded": False,
    }


def test_setup_logging_writes_json_and_does_not_duplicate_handlers() -> None:
    stream = StringIO()
    logger = logging.getLogger("assistant_core")
    original_handlers = logger.handlers[:]
    original_level = logger.level
    original_propagate = logger.propagate
    logger.handlers.clear()

    try:
        configured = setup_logging("DEBUG", stream=stream)
        setup_logging("DEBUG", stream=stream)
        configured.info("handled", extra={"intent": "office", "question": "private user text"})

        assert configured is logger
        assert len(logger.handlers) == 1
        output = json.loads(stream.getvalue())
        assert output["level"] == "INFO"
        assert output["msg"] == "handled"
        assert output["intent"] == "office"
        assert "question" not in output
    finally:
        for handler in logger.handlers:
            if handler not in original_handlers:
                handler.close()
        logger.handlers[:] = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate
