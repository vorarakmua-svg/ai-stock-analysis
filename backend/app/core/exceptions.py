"""Global exception handlers.

Maps the app's domain exceptions to stable HTTP statuses and — crucially —
prevents unexpected exceptions from leaking internal details (str(e)) into 500
response bodies. Every error response carries the request id for correlation.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": get_request_id()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain + catch-all exception handlers on the app."""
    # Imported here to avoid import cycles at module load.
    from app.services.ai_analyst import (
        AnalysisError,
        GeminiAnalysisError,
        InvalidAnalysisError,
        ValuationNotFoundError,
    )
    from app.services.ai_extractor import (
        APIKeyNotConfiguredError,
        DataNotFoundError,
        ExtractionError,
        GeminiAPIError,
        InvalidResponseError,
    )
    from app.services.valuation_engine import InsufficientDataError, ValuationError

    # (exception type, status). More specific subclasses are resolved first via
    # the exception's MRO, so listing both a subclass and its base is fine.
    status_map: list[tuple[type[Exception], int]] = [
        (APIKeyNotConfiguredError, 503),
        (GeminiAPIError, 503),
        (GeminiAnalysisError, 503),
        (DataNotFoundError, 404),
        (ValuationNotFoundError, 404),
        (InsufficientDataError, 422),
        (InvalidResponseError, 502),
        (InvalidAnalysisError, 502),
        (ExtractionError, 500),
        (ValuationError, 500),
        (AnalysisError, 500),
    ]

    def _make_handler(status_code: int):
        async def handler(request: Request, exc: Exception) -> JSONResponse:
            # Domain exceptions carry messages we authored, so surfacing them is
            # safe and useful. Server-class errors are logged at error level.
            log = logger.error if status_code >= 500 else logger.warning
            log("Handled %s: %s", exc.__class__.__name__, exc)
            return _error_response(status_code, str(exc))

        return handler

    for exc_type, code in status_map:
        app.add_exception_handler(exc_type, _make_handler(code))

    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internal details for unanticipated errors.
        logger.exception("Unhandled exception")
        return _error_response(500, "Internal server error")

    app.add_exception_handler(Exception, handle_unexpected)
