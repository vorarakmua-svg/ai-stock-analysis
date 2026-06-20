"""Output contract for per-stock JSON files.

This is the schema the backend consumes (a clean, validated subset of the legacy
collector's output). Extra keys are allowed so the file can grow without breaking
validation, but the fields below are guaranteed when present.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompanyInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    ticker: str
    sector: str | None = None
    industry: str | None = None
    description: str | None = None
    currency: str = "USD"
    exchange: str | None = None


class MarketData(BaseModel):
    model_config = ConfigDict(extra="allow")

    current_price: float | None = None
    previous_close: float | None = None
    market_cap: float | None = None
    beta: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    volume: float | None = None


class Shareholders(BaseModel):
    model_config = ConfigDict(extra="allow")

    shares_outstanding: float | None = None
    float_shares: float | None = None


class StockDataFile(BaseModel):
    """Top-level contract for data/output/json/{TICKER}.json."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    cik: str
    company_name: str
    collected_at: str
    company_info: CompanyInfo
    market_data: MarketData
    shareholders: Shareholders = Field(default_factory=Shareholders)
    # year (str) -> {human-readable financial field: value}
    financials_annual: dict[str, dict] = Field(default_factory=dict)
    data_sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
