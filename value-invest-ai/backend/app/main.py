from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import get_settings
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Initialize database tables
    await init_db()
    print("Database tables initialized")
    yield
    # Shutdown: Cleanup if needed
    print("Application shutting down")


app = FastAPI(
    title="ValueInvestAI",
    description="A Professional Stock Analysis Platform for Value Investors",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ValueInvestAI API",
        "docs": "/docs",
        "health": "/health",
    }


# API v1 router placeholder
@app.get(f"{settings.api_v1_prefix}/companies")
async def list_companies():
    """List all tracked companies (placeholder)."""
    return {"companies": [], "message": "Endpoint placeholder - implementation pending"}


@app.get(f"{settings.api_v1_prefix}/financials/{{ticker}}")
async def get_financials(ticker: str):
    """Get financial data for a company (placeholder)."""
    return {"ticker": ticker, "message": "Endpoint placeholder - implementation pending"}


@app.get(f"{settings.api_v1_prefix}/valuations/{{ticker}}")
async def get_valuations(ticker: str):
    """Get valuation metrics for a company (placeholder)."""
    return {"ticker": ticker, "message": "Endpoint placeholder - implementation pending"}
