"""
FastAPI application entry point for Intelligent Investor Pro.

This module creates and configures the FastAPI application with:
- CORS middleware for frontend communication
- GZip compression for response optimization
- Rate limiting for API protection
- API versioned routing
- Health check endpoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.v1 import api_router
from app.config import get_settings

settings = get_settings()

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
    # Startup: Initialize resources
    import sys
    import io
    # Handle Unicode paths safely for Windows console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print(f"Starting Intelligent Investor Pro API in {settings.APP_ENV} mode")
    print(f"Data directory configured: {settings.DATA_DIR}")
    print(f"CSV path configured: {settings.CSV_PATH}")
    print(f"JSON directory configured: {settings.JSON_DIR}")

    yield

    # Shutdown: Cleanup resources
    print("Shutting down Intelligent Investor Pro API")


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
    response_model=Dict[str, str],
)
async def health_check() -> Dict[str, str]:
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
    "/",
    tags=["Root"],
    summary="API Root",
    description="Root endpoint with API information.",
    response_model=Dict[str, str],
)
async def root() -> Dict[str, str]:
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
