"""
ValueInvestAI - Main FastAPI Application

A Professional Stock Analysis Platform for Value Investors.
Provides 30 years of financial history for US and Thai stocks,
automated valuation models, and AI-powered investment analysis.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import get_settings
from app.database import init_db, check_db_connection, get_db_info
from app.api.v1.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup:
    - Initialize database tables
    - Verify database connection

    Shutdown:
    - Cleanup resources if needed
    """
    # Startup
    print("Starting ValueInvestAI API...")
    await init_db()
    print("Database tables initialized")

    # Check database connection
    if await check_db_connection():
        print("Database connection verified")
    else:
        print("WARNING: Database connection failed!")

    yield

    # Shutdown
    print("Shutting down ValueInvestAI API...")


app = FastAPI(
    title="ValueInvestAI",
    description="A Professional Stock Analysis Platform for Value Investors. "
                "Provides 30 years of financial history for US (NYSE/NASDAQ) and Thai (SET) stocks, "
                "automated valuation models (DCF, Graham Number, Peter Lynch Fair Value), "
                "and AI-powered investment analysis using Warren Buffett's principles.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the application health status including:
    - Overall status
    - Database connection status
    - Application version
    - Environment
    - Timestamp
    """
    db_connected = await check_db_connection()

    return {
        "status": "healthy" if db_connected else "degraded",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/health/detailed", tags=["Health"])
async def health_check_detailed():
    """
    Detailed health check endpoint.

    Returns comprehensive health information including database details.
    This endpoint may be slower as it queries additional database info.
    """
    db_info = await get_db_info()

    return {
        "status": "healthy" if db_info.get("connected") else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
        "database": db_info,
        "services": {
            "api": "running",
            "database": "connected" if db_info.get("connected") else "disconnected",
        }
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information and navigation.
    """
    return {
        "name": "ValueInvestAI API",
        "description": "A Professional Stock Analysis Platform for Value Investors",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "health": "/health",
            "companies": f"{settings.api_v1_prefix}/companies",
            "financials": f"{settings.api_v1_prefix}/financials",
            "valuations": f"{settings.api_v1_prefix}/valuations",
        }
    }
