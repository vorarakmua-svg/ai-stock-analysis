"""
Endpoint tests via TestClient.

The valuation endpoint's exception->HTTP mapping is the valuable routing logic;
we exercise it by overriding the engine dependency with stubs that raise the
domain exceptions. The deterministic math is covered by the unit tests, so we
don't re-serialize a full ValuationResult here.
"""

import pytest

from app.main import app
from app.services.ai_extractor import (
    APIKeyNotConfiguredError,
    DataNotFoundError,
    GeminiAPIError,
)
from app.services.valuation_engine import ValuationError, get_valuation_engine

VAL_URL = "/api/v1/stocks/AAPL/valuation"


def _engine_raising(exc: Exception):
    class _StubEngine:
        async def calculate_valuation(self, ticker, force_refresh=False):
            raise exc

    return lambda: _StubEngine()


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "documentation" in resp.json()


def test_valuation_not_found_maps_to_404(client):
    app.dependency_overrides[get_valuation_engine] = _engine_raising(DataNotFoundError("missing"))
    resp = client.get(VAL_URL)
    assert resp.status_code == 404


def test_valuation_api_key_missing_maps_to_503(client):
    app.dependency_overrides[get_valuation_engine] = _engine_raising(
        APIKeyNotConfiguredError("no key")
    )
    resp = client.get(VAL_URL)
    assert resp.status_code == 503


def test_valuation_gemini_error_maps_to_503(client):
    app.dependency_overrides[get_valuation_engine] = _engine_raising(
        GeminiAPIError("upstream down")
    )
    resp = client.get(VAL_URL)
    assert resp.status_code == 503


def test_valuation_engine_error_maps_to_500(client):
    app.dependency_overrides[get_valuation_engine] = _engine_raising(ValuationError("bad math"))
    resp = client.get(VAL_URL)
    assert resp.status_code == 500
