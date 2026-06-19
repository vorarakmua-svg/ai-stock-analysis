"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def engine(tmp_path):
    """
    A ValuationEngine backed by a throwaway on-disk cache.

    The deterministic math methods (calculate_wacc/dcf/graham/etc.) never touch
    the cache or the AI extractor, so this is safe and offline.
    """
    from app.services.valuation_engine import ValuationCache, ValuationEngine

    return ValuationEngine(cache=ValuationCache(cache_dir=tmp_path / "valcache"))
