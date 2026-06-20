"""Validate produced stock data against the output contract before writing."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from ingestion.schemas import StockDataFile


class ValidationFailed(Exception):
    """Raised when produced data does not satisfy the output contract."""


def validate_stock_data(data: dict[str, Any]) -> StockDataFile:
    """Return a validated StockDataFile, or raise ValidationFailed."""
    try:
        return StockDataFile.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailed(str(exc)) from exc
