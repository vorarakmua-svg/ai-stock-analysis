"""
API v1 router aggregating all endpoint modules.

Combines all endpoint routers into a single API router
with appropriate prefixes and tags.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analysis, extraction, realtime, screener, stock, valuation

api_router = APIRouter()

# Include screener endpoints (GET /stocks, GET /stocks/metadata)
api_router.include_router(
    screener.router,
    prefix="/stocks",
    tags=["Screener"],
)

# Include stock detail endpoints (GET /stocks/{ticker})
api_router.include_router(
    stock.router,
    prefix="/stocks",
    tags=["Stock Details"],
)

# Include real-time data endpoints (GET /stocks/{ticker}/price, GET /stocks/{ticker}/history)
api_router.include_router(
    realtime.router,
    prefix="/stocks",
    tags=["Real-Time Data"],
)

# Include AI extraction endpoints (GET /stocks/{ticker}/extraction)
api_router.include_router(
    extraction.router,
    prefix="/stocks",
    tags=["AI Extraction"],
)

# Include valuation endpoints (GET /stocks/{ticker}/valuation, POST /stocks/{ticker}/valuation/refresh)
api_router.include_router(
    valuation.router,
    prefix="/stocks",
    tags=["Valuation"],
)

# Include AI analysis endpoints (GET /stocks/{ticker}/analysis, POST /stocks/{ticker}/analysis/refresh)
api_router.include_router(
    analysis.router,
    prefix="/stocks",
    tags=["AI Analysis"],
)
