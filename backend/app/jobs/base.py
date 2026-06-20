"""Job queue abstraction (decouples HTTP layer from arq)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# Normalized job states surfaced to clients.
QUEUED = "queued"
IN_PROGRESS = "in_progress"
COMPLETE = "complete"
FAILED = "failed"
NOT_FOUND = "not_found"


@dataclass
class JobState:
    job_id: str
    status: str
    result: Any | None = None
    error: str | None = None


@runtime_checkable
class JobQueue(Protocol):
    async def enqueue_valuation(self, ticker: str, force_refresh: bool = False) -> str:
        """Enqueue a valuation job; return its job id."""
        ...

    async def get_state(self, job_id: str) -> JobState:
        """Return the current state (and result/error if finished)."""
        ...
