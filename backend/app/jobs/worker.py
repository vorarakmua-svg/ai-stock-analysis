"""arq worker definition.

Run with:  arq app.jobs.worker.WorkerSettings
The worker shares the Redis configured for the app (REDIS_URL).
"""

from __future__ import annotations

import logging
from typing import Any

from arq.connections import RedisSettings

from app.config import get_settings

logger = logging.getLogger(__name__)


async def run_valuation(ctx: dict, ticker: str, force_refresh: bool = False) -> dict[str, Any]:
    """Compute a valuation off the request path; arq stores the returned dict."""
    from app.services.valuation_engine import get_valuation_engine

    logger.info("Job run_valuation start: %s (force_refresh=%s)", ticker, force_refresh)
    engine = get_valuation_engine()
    result = await engine.calculate_valuation(ticker, force_refresh=force_refresh)
    logger.info("Job run_valuation done: %s", ticker)
    return result.model_dump(mode="json")


def _redis_settings() -> RedisSettings:
    url = get_settings().REDIS_URL or "redis://localhost:6379/0"
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    """arq worker configuration."""

    functions = [run_valuation]
    redis_settings = _redis_settings()
