"""
Tests for P4 observability/hardening: exception handlers, request-id header,
readiness, and metrics.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.exceptions import register_exception_handlers
from app.middleware.request_id import REQUEST_ID_HEADER
from app.services.ai_extractor import DataNotFoundError


# ---------------------------------------------------------------------------
# Global exception handlers (isolated throwaway app)
# ---------------------------------------------------------------------------
@pytest.fixture
def handler_client():
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/boom-domain")
    async def boom_domain():
        raise DataNotFoundError("ticker XYZ not found")

    @test_app.get("/boom-generic")
    async def boom_generic():
        raise RuntimeError("super secret internal detail")

    return TestClient(test_app, raise_server_exceptions=False)


def test_domain_exception_maps_to_status_and_keeps_message(handler_client):
    resp = handler_client.get("/boom-domain")
    assert resp.status_code == 404
    body = resp.json()
    assert "not found" in body["detail"]
    assert "request_id" in body


def test_unexpected_exception_is_generic_and_does_not_leak(handler_client):
    resp = handler_client.get("/boom-generic")
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    # The internal message must NOT leak to the client.
    assert "secret internal detail" not in resp.text
    assert "request_id" in body


# ---------------------------------------------------------------------------
# Request-id, readiness, metrics on the real app
# ---------------------------------------------------------------------------
def test_request_id_header_present(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get(REQUEST_ID_HEADER)


def test_inbound_request_id_is_echoed(client):
    resp = client.get("/health", headers={REQUEST_ID_HEADER: "abc123"})
    assert resp.headers.get(REQUEST_ID_HEADER) == "abc123"


def test_ready_returns_200_when_healthy(client, monkeypatch):
    monkeypatch.setattr(main_module, "check_readiness", lambda: (True, {"data_dir": "ok"}))
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_ready_returns_503_when_dependency_missing(client, monkeypatch):
    monkeypatch.setattr(main_module, "check_readiness", lambda: (False, {"data_dir": "missing"}))
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["checks"]["data_dir"] == "missing"


def test_metrics_endpoint_exposes_prometheus(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text


# ---------------------------------------------------------------------------
# Readiness + logging units
# ---------------------------------------------------------------------------
def test_check_readiness_logic(tmp_path, monkeypatch):
    import app.core.health as health

    class _FakeSettings:
        def __init__(self, key, json_dir):
            self.GOOGLE_API_KEY = key
            self._json_dir = json_dir

        @property
        def json_dir_resolved(self):
            return self._json_dir

    # Healthy: key set + a data dir with a json file.
    (tmp_path / "AAPL.json").write_text("{}")
    monkeypatch.setattr(health, "get_settings", lambda: _FakeSettings("k", tmp_path))
    healthy, checks = health.check_readiness()
    assert healthy is True
    assert checks == {"google_api_key": "ok", "data_dir": "ok"}

    # Unhealthy: no key, empty dir.
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(health, "get_settings", lambda: _FakeSettings("", empty))
    healthy, checks = health.check_readiness()
    assert healthy is False
    assert checks["google_api_key"] == "missing"
    assert checks["data_dir"] == "missing"


def test_configure_logging_installs_single_handler():
    import logging

    from app.core.logging_config import configure_logging

    configure_logging(level="DEBUG", json_enabled=True)
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.DEBUG
    # Idempotent: a second call doesn't stack handlers.
    configure_logging(level="INFO", json_enabled=False)
    assert len(root.handlers) == 1
