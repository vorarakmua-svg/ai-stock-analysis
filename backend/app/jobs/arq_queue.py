"""arq-backed JobQueue implementation + FastAPI dependency."""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.jobs.base import (
    COMPLETE,
    FAILED,
    IN_PROGRESS,
    NOT_FOUND,
    QUEUED,
    JobState,
)

logger = logging.getLogger(__name__)


class ArqJobQueue:
    """Wraps an arq Redis pool behind the JobQueue protocol."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def enqueue_valuation(self, ticker: str, force_refresh: bool = False) -> str:
        job = await self._pool.enqueue_job("run_valuation", ticker, force_refresh)
        return job.job_id

    async def get_state(self, job_id: str) -> JobState:
        from arq.jobs import Job, JobStatus

        job = Job(job_id, self._pool)
        status = await job.status()

        if status == JobStatus.not_found:
            return JobState(job_id, NOT_FOUND)
        if status == JobStatus.complete:
            try:
                result = await job.result(timeout=0.1)
                return JobState(job_id, COMPLETE, result=result)
            except Exception as exc:  # task raised -> failed
                return JobState(job_id, FAILED, error=str(exc))
        if status == JobStatus.in_progress:
            return JobState(job_id, IN_PROGRESS)
        # queued / deferred
        return JobState(job_id, QUEUED)


# Lazily-created shared pool (arq pools are async; can't use lru_cache).
_pool: Any | None = None


async def get_job_queue() -> ArqJobQueue:
    """FastAPI dependency. Raises if the job queue (Redis) isn't configured."""
    from fastapi import HTTPException, status

    settings = get_settings()
    if not settings.REDIS_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Async job queue is not configured (set REDIS_URL).",
        )

    global _pool
    if _pool is None:
        from arq import create_pool
        from arq.connections import RedisSettings

        _pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return ArqJobQueue(_pool)
