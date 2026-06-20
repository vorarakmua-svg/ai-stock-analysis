"""Per-request context propagated via contextvars (works across async hops)."""

from __future__ import annotations

from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the current request id, or '-' outside a request."""
    return _request_id.get()


def set_request_id(value: str) -> None:
    """Set the request id for the current context."""
    _request_id.set(value)
