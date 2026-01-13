"""
Data loading utilities for CSV and JSON financial data.

This module provides functions to load and parse stock data from:
- summary.csv: Aggregated stock data for screener
- {TICKER}.json: Detailed financial data per stock
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.config import get_settings

logger = logging.getLogger(__name__)

# Maximum file size for JSON files (10MB) to prevent memory exhaustion
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024

settings = get_settings()


class DataLoadError(Exception):
    """Custom exception for data loading errors."""

    pass


def load_summary_csv() -> List[Dict[str, Any]]:
    """
    Load summary.csv as a list of dictionaries.

    Each row becomes a dictionary with column names as keys.
    Handles NaN values by converting them to None.

    Returns:
        List of dictionaries, one per stock row.

    Raises:
        DataLoadError: If the CSV file cannot be loaded.

    Example:
        >>> stocks = load_summary_csv()
        >>> stocks[0]['ticker']
        'NVDA'
    """
    csv_path = settings.csv_path_resolved

    if not csv_path.exists():
        raise DataLoadError(f"Summary CSV not found at: {csv_path}")

    try:
        df = pd.read_csv(csv_path)

        # Replace NaN/inf values with None for JSON serialization
        import numpy as np
        df = df.replace([np.nan, np.inf, -np.inf], None)

        # Convert to list of dictionaries
        records = df.to_dict(orient="records")

        # Double-check for any remaining float NaN values and convert to None
        # Also normalize debt_to_equity from percentage to ratio (yfinance returns %)
        def sanitize_record(record: Dict[str, Any]) -> Dict[str, Any]:
            sanitized = {}
            for key, value in record.items():
                if isinstance(value, float) and (pd.isna(value) or np.isinf(value)):
                    sanitized[key] = None
                # debt_to_equity from yfinance is in percentage (75.73 = 75.73%)
                # Convert to ratio (0.7573) for consistency
                elif key == "debt_to_equity" and value is not None:
                    sanitized[key] = value / 100.0
                else:
                    sanitized[key] = value
            return sanitized

        records = [sanitize_record(r) for r in records]

        return records

    except pd.errors.EmptyDataError:
        raise DataLoadError(f"Summary CSV is empty: {csv_path}")
    except Exception as e:
        raise DataLoadError(f"Failed to load summary CSV: {e}") from e


@lru_cache(maxsize=32)
def load_stock_json(ticker: str) -> Dict[str, Any]:
    """
    Load individual stock JSON file by ticker symbol.

    Uses LRU cache to avoid repeated file reads for frequently accessed stocks.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA').

    Returns:
        Dictionary containing all financial data for the stock.

    Raises:
        DataLoadError: If the JSON file cannot be loaded or parsed.

    Example:
        >>> data = load_stock_json('AAPL')
        >>> data['company_info']['name']
        'Apple Inc.'
    """
    json_dir = settings.json_dir_resolved
    json_path = json_dir / f"{ticker.upper()}.json"

    if not json_path.exists():
        raise DataLoadError(f"Stock JSON not found for ticker: {ticker}")

    # Check file size to prevent memory exhaustion from malformed/large files
    file_size = json_path.stat().st_size
    if file_size > MAX_JSON_FILE_SIZE:
        logger.warning(
            "JSON file for %s exceeds size limit: %d bytes (max: %d)",
            ticker, file_size, MAX_JSON_FILE_SIZE
        )
        raise DataLoadError(
            f"JSON file for ticker {ticker} exceeds maximum size limit ({file_size} > {MAX_JSON_FILE_SIZE} bytes)"
        )

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize debt_to_equity from percentage to ratio (yfinance returns %)
        # Check in valuation section where yfinance data is stored
        if "valuation" in data and data["valuation"].get("debt_to_equity") is not None:
            data["valuation"]["debt_to_equity"] = data["valuation"]["debt_to_equity"] / 100.0

        return data

    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON for ticker {ticker}: {e}") from e
    except Exception as e:
        raise DataLoadError(f"Failed to load JSON for ticker {ticker}: {e}") from e


def get_available_tickers() -> List[str]:
    """
    List all available stock tickers from JSON directory.

    Scans the JSON directory for .json files and extracts ticker symbols
    from filenames.

    Returns:
        Sorted list of available ticker symbols.

    Raises:
        DataLoadError: If the JSON directory doesn't exist.

    Example:
        >>> tickers = get_available_tickers()
        >>> tickers
        ['AAPL', 'AMZN', 'AVGO', 'BRK-B', 'GOOGL', 'LLY', 'META', 'MSFT', 'NVDA', 'TSLA']
    """
    json_dir = settings.json_dir_resolved

    if not json_dir.exists():
        raise DataLoadError(f"JSON directory not found: {json_dir}")

    tickers = []
    for json_file in json_dir.glob("*.json"):
        # Extract ticker from filename (e.g., "AAPL.json" -> "AAPL")
        ticker = json_file.stem
        tickers.append(ticker)

    return sorted(tickers)


def get_stock_by_ticker(ticker: str, stocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Find a stock in the summary data by ticker symbol.

    Args:
        ticker: Stock ticker symbol to search for.
        stocks: Optional pre-loaded list of stocks. If None, loads from CSV.

    Returns:
        Stock dictionary if found, None otherwise.

    Example:
        >>> stock = get_stock_by_ticker('AAPL')
        >>> stock['company_name']
        'Apple Inc.'
    """
    if stocks is None:
        stocks = load_summary_csv()

    ticker_upper = ticker.upper()
    for stock in stocks:
        if stock.get("ticker", "").upper() == ticker_upper:
            return stock

    return None


def get_unique_sectors(stocks: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Get list of unique sectors from stock data.

    Args:
        stocks: Optional pre-loaded list of stocks. If None, loads from CSV.

    Returns:
        Sorted list of unique sector names.

    Example:
        >>> sectors = get_unique_sectors()
        >>> 'Technology' in sectors
        True
    """
    if stocks is None:
        stocks = load_summary_csv()

    sectors = set()
    for stock in stocks:
        sector = stock.get("sector")
        if sector:
            sectors.add(sector)

    return sorted(sectors)


def get_unique_industries(stocks: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Get list of unique industries from stock data.

    Args:
        stocks: Optional pre-loaded list of stocks. If None, loads from CSV.

    Returns:
        Sorted list of unique industry names.

    Example:
        >>> industries = get_unique_industries()
        >>> 'Semiconductors' in industries
        True
    """
    if stocks is None:
        stocks = load_summary_csv()

    industries = set()
    for stock in stocks:
        industry = stock.get("industry")
        if industry:
            industries.add(industry)

    return sorted(industries)


def get_column_names() -> List[str]:
    """
    Get list of all column names from summary CSV.

    Returns:
        List of column names in order.

    Example:
        >>> columns = get_column_names()
        >>> 'ticker' in columns
        True
    """
    csv_path = settings.csv_path_resolved

    if not csv_path.exists():
        raise DataLoadError(f"Summary CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path, nrows=0)
    return df.columns.tolist()


def clear_json_cache() -> None:
    """
    Clear the LRU cache for stock JSON files.

    Call this if JSON files are updated and need to be reloaded.
    """
    load_stock_json.cache_clear()
