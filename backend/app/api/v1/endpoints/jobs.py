"""Async valuation endpoints (enqueue + poll), backed by the job queue."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.jobs.arq_queue import get_job_queue
from app.jobs.base import NOT_FOUND, JobQueue

logger = logging.getLogger(__name__)

router = APIRouter()

TickerPath = Annotated[str, Path(..., min_length=1, max_length=10, examples=["AAPL"])]


@router.post(
    "/stocks/{ticker}/valuation/async",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Jobs"],
    summary="Enqueue an async valuation",
)
async def enqueue_valuation(
    ticker: TickerPath,
    queue: JobQueue = Depends(get_job_queue),
) -> dict:
    """Queue a valuation computation; returns a job id to poll."""
    job_id = await queue.enqueue_valuation(ticker.upper().strip())
    logger.info("Enqueued valuation job %s for %s", job_id, ticker)
    return {"job_id": job_id, "status": "queued"}


@router.get(
    "/jobs/{job_id}",
    tags=["Jobs"],
    summary="Get job status / result",
)
async def get_job(
    job_id: str,
    queue: JobQueue = Depends(get_job_queue),
) -> dict:
    """Return job status; includes the result once complete."""
    state = await queue.get_state(job_id)
    if state.status == NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {
        "job_id": state.job_id,
        "status": state.status,
        "result": state.result,
        "error": state.error,
    }
