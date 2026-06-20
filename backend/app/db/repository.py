"""Best-effort persistence helpers.

Each function is a no-op when the DB is disabled and swallows errors so that a
persistence hiccup never breaks the request path (the cache remains the read path).
"""

from __future__ import annotations

import logging
from typing import Any

from app.db import models
from app.db.session import get_sessionmaker, is_enabled

logger = logging.getLogger(__name__)


async def save_valuation(
    *,
    ticker: str,
    composite_intrinsic_value: float | None,
    verdict: str | None,
    extraction_timestamp: str | None,
    payload: dict[str, Any],
    owner_id: str | None = None,
) -> None:
    """Persist a valuation result (best-effort)."""
    if not is_enabled():
        return
    try:
        async with get_sessionmaker()() as session:
            session.add(
                models.Valuation(
                    ticker=ticker,
                    composite_intrinsic_value=composite_intrinsic_value,
                    verdict=verdict,
                    extraction_timestamp=extraction_timestamp,
                    payload=payload,
                    owner_id=owner_id,
                )
            )
            await session.commit()
    except Exception:  # pragma: no cover - persistence must never break a request
        logger.exception("Failed to persist valuation for %s", ticker)


async def save_llm_usage(
    *,
    purpose: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int,
    total_tokens: int,
    ticker: str | None = None,
    owner_id: str | None = None,
) -> None:
    """Persist a single LLM usage record (best-effort metering)."""
    if not is_enabled():
        return
    try:
        async with get_sessionmaker()() as session:
            session.add(
                models.LlmUsage(
                    purpose=purpose,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    thinking_tokens=thinking_tokens,
                    total_tokens=total_tokens,
                    ticker=ticker,
                    owner_id=owner_id,
                )
            )
            await session.commit()
    except Exception:  # pragma: no cover
        logger.exception("Failed to persist llm usage (%s)", purpose)
