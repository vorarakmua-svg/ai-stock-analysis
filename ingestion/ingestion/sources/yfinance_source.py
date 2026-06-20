"""Thin yfinance wrapper for market data + company info.

Kept small and side-effect-isolated so it is trivially mockable in tests (the
network call lives only in ``fetch_market_snapshot``).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def fetch_market_snapshot(ticker: str) -> dict[str, Any]:
    """Return a normalized snapshot of market + company info from yfinance."""
    import yfinance as yf

    info = yf.Ticker(ticker).info or {}
    return normalize_info(info)


def normalize_info(info: dict[str, Any]) -> dict[str, Any]:
    """Map a yfinance ``.info`` dict to our market_data / company_info shape.

    Pure function (no network) so it can be unit-tested directly.
    """
    market_data = {
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "market_cap": info.get("marketCap"),
        "beta": info.get("beta"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
    }
    company_info = {
        "name": info.get("longName") or info.get("shortName") or "",
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": info.get("longBusinessSummary"),
        "currency": info.get("currency") or "USD",
        "exchange": info.get("exchange"),
    }
    shareholders = {
        "shares_outstanding": info.get("sharesOutstanding"),
        "float_shares": info.get("floatShares"),
    }
    return {
        "market_data": market_data,
        "company_info": company_info,
        "shareholders": shareholders,
    }
