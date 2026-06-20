"""Tests for async job endpoints + the worker task. No live Redis/worker."""

import pytest

from app.api.v1.endpoints.jobs import get_job_queue
from app.jobs.base import COMPLETE, NOT_FOUND, QUEUED, JobState
from app.main import app


class FakeQueue:
    def __init__(self, state: JobState | None = None):
        self.enqueued: list[tuple[str, bool]] = []
        self._state = state

    async def enqueue_valuation(self, ticker: str, force_refresh: bool = False) -> str:
        self.enqueued.append((ticker, force_refresh))
        return "job-123"

    async def get_state(self, job_id: str) -> JobState:
        return self._state or JobState(job_id, NOT_FOUND)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_enqueue_returns_202_and_job_id(client):
    fake = FakeQueue()
    app.dependency_overrides[get_job_queue] = lambda: fake

    resp = client.post("/api/v1/stocks/AAPL/valuation/async")

    assert resp.status_code == 202
    assert resp.json() == {"job_id": "job-123", "status": "queued"}
    assert fake.enqueued == [("AAPL", False)]


def test_job_status_queued(client):
    app.dependency_overrides[get_job_queue] = lambda: FakeQueue(JobState("job-1", QUEUED))
    resp = client.get("/api/v1/jobs/job-1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


def test_job_status_complete_returns_result(client):
    state = JobState("job-1", COMPLETE, result={"composite_intrinsic_value": 158.0})
    app.dependency_overrides[get_job_queue] = lambda: FakeQueue(state)
    resp = client.get("/api/v1/jobs/job-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "complete"
    assert body["result"]["composite_intrinsic_value"] == 158.0


def test_job_status_not_found_maps_to_404(client):
    app.dependency_overrides[get_job_queue] = lambda: FakeQueue(JobState("x", NOT_FOUND))
    resp = client.get("/api/v1/jobs/x")
    assert resp.status_code == 404


def test_enqueue_503_when_queue_not_configured(client, monkeypatch):
    # No override -> real get_job_queue dependency; REDIS_URL empty -> 503.
    from app.config import get_settings

    monkeypatch.delenv("REDIS_URL", raising=False)
    get_settings.cache_clear()
    try:
        resp = client.post("/api/v1/stocks/AAPL/valuation/async")
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()


# --- worker task ------------------------------------------------------------
async def test_run_valuation_task_calls_engine(monkeypatch):
    import app.jobs.worker as worker

    class _Result:
        def model_dump(self, mode="json"):
            return {"ticker": "AAPL", "composite_intrinsic_value": 158.0}

    class _Engine:
        async def calculate_valuation(self, ticker, force_refresh=False):
            assert ticker == "AAPL"
            return _Result()

    monkeypatch.setattr("app.services.valuation_engine.get_valuation_engine", lambda: _Engine())
    out = await worker.run_valuation({}, "AAPL", False)
    assert out == {"ticker": "AAPL", "composite_intrinsic_value": 158.0}
