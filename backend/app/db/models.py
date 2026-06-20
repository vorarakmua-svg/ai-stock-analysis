"""ORM models.

Design notes:
- JSON columns use the generic SQLAlchemy JSON type so the same models work on
  Postgres (JSONB-backed) and SQLite (used in tests) without changes.
- Every user-facing row carries a nullable ``owner_id`` placeholder so adding
  auth/multi-tenancy later is an additive (non-breaking) migration.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Valuation(Base):
    """A computed valuation result (history + queryability + metering substrate)."""

    __tablename__ = "valuations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    composite_intrinsic_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Extraction(Base):
    """A normalized extraction snapshot for a ticker."""

    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    collected_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LlmUsage(Base):
    """Per-call LLM token usage (the metering substrate for future billing)."""

    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    purpose: Mapped[str] = mapped_column(String(64), index=True)
    ticker: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    thinking_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IngestionRun(Base):
    """A record of a data-pipeline run (manifest summary)."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[str] = mapped_column(String(64))
    total: Mapped[int] = mapped_column(Integer, default=0)
    written: Mapped[int] = mapped_column(Integer, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
