"""
API v1 Router - Main router that aggregates all v1 endpoints.

This module combines all API v1 endpoint routers into a single router
that is mounted at /api/v1 in the main application.
"""

from fastapi import APIRouter

from app.api.v1 import companies, financials, valuations

# Create main v1 router
api_router = APIRouter()

# Include sub-routers with their prefixes and tags
api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["Companies"],
)

api_router.include_router(
    financials.router,
    prefix="/financials",
    tags=["Financials"],
)

api_router.include_router(
    valuations.router,
    prefix="/valuations",
    tags=["Valuations"],
)
