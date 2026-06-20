"""Async job processing (arq).

Moves the slow (10-60s) AI valuation pipeline off the request path. The HTTP
layer depends on the ``JobQueue`` protocol, so endpoints are testable without a
live Redis/worker; ``ArqJobQueue`` is the concrete implementation.
"""

from app.jobs.base import JobQueue, JobState

__all__ = ["JobQueue", "JobState"]
