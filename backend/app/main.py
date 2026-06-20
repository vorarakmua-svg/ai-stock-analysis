"""
FastAPI application entry point for Intelligent Investor Pro.

This module creates and configures the FastAPI application with:
- CORS middleware for frontend communication
- GZip compression for response optimization
- Rate limiting for API protection
- API versioned routing
- Health check endpoint
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import api_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.health import check_readiness
from app.core.logging_config import configure_logging
from app.core.metrics import MetricsMiddleware, metrics_response
from app.middleware.request_id import RequestIDMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    """Initialize Sentry if a DSN is configured and the SDK is installed."""
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
        logger.info("Sentry error tracking enabled")
    except Exception:  # pragma: no cover - optional dependency
        logger.warning("SENTRY_DSN set but sentry_sdk unavailable; skipping")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None: After startup tasks complete.

    Note:
        Use this for initializing connections, caches, or other resources
        that need cleanup on shutdown.
    """
    # Startup: configure structured logging and optional error tracking.
    configure_logging(level=settings.LOG_LEVEL, json_enabled=settings.LOG_JSON)
    _init_sentry()

    logger.info(
        "Starting Intelligent Investor Pro API (env=%s, json_dir=%s)",
        settings.APP_ENV,
        settings.JSON_DIR,
    )

    yield

    # Shutdown: Cleanup resources
    logger.info("Shutting down Intelligent Investor Pro API")


app = FastAPI(
    title="Intelligent Investor Pro API",
    description=(
        "A local-first stock analysis API combining AI-powered data normalization "
        "with CFA-grade valuation methodologies. Provides stock screening, "
        "detailed financials, DCF/Graham valuations, and Warren Buffett-style analysis."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handlers (domain -> status; catch-all hides internals)
register_exception_handlers(app)

# Request-ID correlation (outermost so it wraps everything) and metrics.
app.add_middleware(RequestIDMiddleware)
if settings.ENABLE_METRICS:
    app.add_middleware(MetricsMiddleware)

# Configure GZip compression (compress responses > 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Configure CORS middleware with restricted methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Only methods we actually use
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# Include API router with version prefix
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running and healthy.",
    response_model=dict[str, str],
)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Dict with status "healthy" and environment info.
    """
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Verify dependencies (data, API key) are available to serve traffic.",
)
async def readiness_check() -> JSONResponse:
    """Return 200 when ready, 503 (with per-dependency detail) when not."""
    healthy, checks = check_readiness()
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "not_ready", "checks": checks},
    )


if settings.ENABLE_METRICS:

    @app.get("/metrics", tags=["Health"], summary="Prometheus metrics")
    async def metrics():  # noqa: ANN201 - returns a raw exposition response
        return metrics_response()


@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Root endpoint with API information.",
    response_model=dict[str, str],
)
async def root() -> dict[str, str]:
    """
    Root endpoint providing basic API information.

    Returns:
        Dict with API name and documentation URL.
    """
    return {
        "name": "Intelligent Investor Pro API",
        "documentation": "/docs",
        "health": "/health",
        "api_prefix": settings.API_PREFIX,
    }
