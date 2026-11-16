"""Structured logging: every log line is one JSON object, so tools can search it."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Fields every LogRecord already has; anything else was passed with extra={...}.
_STANDARD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        line.update({k: v for k, v in record.__dict__.items() if k not in _STANDARD})
        if record.exc_info:
            line["error"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


def configure_logging(level: str = "WARNING") -> None:
    """Send opsclient logs to stderr as JSON. Results still go to stdout."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("opsclient")
    logger.handlers = [handler]
    logger.setLevel(level.upper())
    logger.propagate = False
