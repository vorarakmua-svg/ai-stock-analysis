"""
Dependency injection for FastAPI endpoints.

Provides reusable dependencies for settings, data loading,
and other shared resources across endpoints.
"""

import re
from typing import Annotated, Any, Dict, List

from fastapi import Depends, HTTPException, Path, status

from app.config import Settings, get_settings
from app.core.data_loader import (
    get_available_tickers,
    load_summary_csv,
    load_stock_json,
)


# Regex pattern for valid ticker symbols (1-10 chars, may include dots or hyphens for class shares)
TICKER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9.\-]{0,9}$")


def validate_ticker_format(ticker: str) -> str:
    """
    Validate ticker symbol format.

    Args:
        ticker: Stock ticker symbol to validate.

    Returns:
        Uppercase ticker if valid format.

    Raises:
        ValueError: If ticker format is invalid.
    """
    ticker_stripped = ticker.strip()

    if not ticker_stripped:
        raise ValueError("Ticker symbol cannot be empty")

    if not TICKER_PATTERN.match(ticker_stripped):
        raise ValueError(
            f"Invalid ticker format: '{ticker}'. "
            "Ticker must start with a letter and contain only letters, numbers, dots, or hyphens (max 10 chars)"
        )

    return ticker_stripped.upper()


# Path parameter with validation for use in endpoints
TickerPath = Annotated[
    str,
    Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA', 'BRK-B')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z][A-Za-z0-9.\-]{0,9}$",
        examples=["AAPL", "NVDA", "MSFT", "BRK-B"],
    ),
]


# Type alias for settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_stocks_data() -> List[Dict[str, Any]]:
    """
    Dependency to load all stocks from summary CSV.

    Returns:
        List of stock dictionaries from summary.csv.

    Note:
        This loads data on each request. For production, consider
        caching the result with a TTL.
    """
    return load_summary_csv()


def get_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Dependency factory to load a specific stock's JSON data.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Full stock financial data dictionary.

    Note:
        Use as: Depends(lambda: get_stock_data(ticker))
    """
    return load_stock_json(ticker)


def get_tickers_list() -> List[str]:
    """
    Dependency to get list of available tickers.

    Returns:
        Sorted list of available stock ticker symbols.
    """
    return get_available_tickers()


# Type aliases for common dependencies
StocksDataDep = Annotated[List[Dict[str, Any]], Depends(get_stocks_data)]
TickersListDep = Annotated[List[str], Depends(get_tickers_list)]


async def verify_ticker_exists(ticker: str) -> str:
    """
    Verify that a ticker exists in the available data.

    Args:
        ticker: Stock ticker symbol to verify.

    Returns:
        Uppercase ticker if valid.

    Raises:
        ValueError: If ticker doesn't exist.
    """
    ticker_upper = ticker.upper()
    available = get_available_tickers()

    if ticker_upper not in available:
        raise ValueError(f"Ticker not found: {ticker_upper}")

    return ticker_upper
