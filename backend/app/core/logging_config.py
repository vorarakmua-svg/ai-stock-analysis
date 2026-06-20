"""Centralized logging configuration (structured JSON or human-readable)."""

from __future__ import annotations

import logging
import sys

try:  # python-json-logger >= 3 moved the formatter
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # pragma: no cover - older versions
    from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """Inject the current request id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging(level: str = "INFO", json_enabled: bool = True) -> None:
    """Configure the root logger with a single stdout handler.

    Idempotent: clears existing handlers so repeated calls (tests, reload) don't
    duplicate output.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if json_enabled:
        formatter: logging.Formatter = JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
        )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
