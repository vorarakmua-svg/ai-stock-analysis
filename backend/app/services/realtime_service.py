"""
Real-time stock data service using yfinance.

Provides functions for fetching real-time price data and historical OHLCV data
with intelligent caching using diskcache to minimize API calls.
"""

import asyncio
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional

import diskcache
import yfinance as yf

from app.config import get_settings

logger = logging.getLogger(__name__)

# Type alias for valid period options
PeriodType = Literal["1mo", "3mo", "6mo", "1y", "5y"]

# Valid periods for historical data
VALID_PERIODS: tuple[PeriodType, ...] = ("1mo", "3mo", "6mo", "1y", "5y")

# Timeout for yfinance API calls (in seconds)
YFINANCE_TIMEOUT: float = 30.0

# Market state mappings from yfinance
MARKET_STATE_MAP: Dict[str, str] = {
    "PRE": "PRE",
    "PREPRE": "PRE",
    "REGULAR": "REGULAR",
    "POST": "POST",
    "POSTPOST": "POST",
    "CLOSED": "CLOSED",
    "": "CLOSED",
}


class RealtimeServiceError(Exception):
    """Base exception for realtime service errors."""

    pass


class TickerNotFoundError(RealtimeServiceError):
    """Raised when the ticker symbol is invalid or not found."""

    pass


class DataFetchError(RealtimeServiceError):
    """Raised when there is an error fetching data from yfinance."""

    pass


@lru_cache(maxsize=1)
def _get_cache() -> diskcache.Cache:
    """
    Get or create the singleton diskcache instance for price caching.

    Uses lru_cache for thread-safe lazy initialization without blocking
    the async event loop.

    Returns:
        diskcache.Cache: Configured cache instance.
    """
    settings = get_settings()
    cache_path = settings.cache_dir_resolved / "price_cache"
    return diskcache.Cache(str(cache_path))


def _normalize_market_state(state: str | None) -> str:
    """
    Normalize yfinance market state to our standard format.

    Args:
        state: Raw market state from yfinance.

    Returns:
        Normalized market state string.
    """
    if state is None:
        return "CLOSED"
    return MARKET_STATE_MAP.get(state.upper(), "CLOSED")


def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, handling None and invalid values.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Float value or default.
    """
    if value is None:
        return default
    try:
        result = float(value)
        # Handle NaN values
        if result != result:  # NaN check
            return default
        return result
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int, handling None and invalid values.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Int value or default.
    """
    if value is None:
        return default
    try:
        result = float(value)  # Handle scientific notation
        if result != result:  # NaN check
            return default
        return int(result)
    except (TypeError, ValueError):
        return default


async def get_realtime_price(ticker: str) -> Dict[str, Any]:
    """
    Get real-time price data for a stock ticker.

    Uses 30-second caching to minimize API calls while providing
    reasonably fresh price data.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT").

    Returns:
        Dictionary containing:
            - ticker: str
            - price: float (current/latest price)
            - change: float (absolute price change)
            - change_percent: float (percentage change)
            - volume: int (trading volume)
            - high: float (day's high)
            - low: float (day's low)
            - open: float (day's open)
            - previous_close: float
            - timestamp: str (ISO format)
            - market_state: str ("PRE", "REGULAR", "POST", "CLOSED")

    Raises:
        TickerNotFoundError: If the ticker is invalid or not found.
        DataFetchError: If there's an error fetching data from yfinance.
    """
    settings = get_settings()
    ticker_upper = ticker.upper().strip()
    cache_key = f"price:{ticker_upper}"

    # Check cache first
    cache = _get_cache()
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.debug(f"Cache hit for {ticker_upper} price data")
        return cached_data

    logger.info(f"Fetching real-time price for {ticker_upper}")

    try:
        # Create ticker object and fetch data (run in thread pool to avoid blocking)
        def fetch_ticker_info() -> Dict[str, Any]:
            stock = yf.Ticker(ticker_upper)
            return stock.info

        try:
            info = await asyncio.wait_for(
                asyncio.to_thread(fetch_ticker_info),
                timeout=YFINANCE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise DataFetchError(
                f"Timeout fetching price data for '{ticker_upper}' after {YFINANCE_TIMEOUT}s"
            )

        if not info or info.get("regularMarketPrice") is None:
            # Try to check if it's a valid ticker by looking for basic info
            if not info.get("shortName") and not info.get("symbol"):
                raise TickerNotFoundError(
                    f"Ticker '{ticker_upper}' not found or has no market data"
                )

        # Extract price data with safe conversions
        current_price = _safe_float(
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("previousClose")
        )
        previous_close = _safe_float(info.get("regularMarketPreviousClose") or info.get("previousClose"))

        # Calculate change
        change = current_price - previous_close if previous_close > 0 else 0.0
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0

        # Get market state
        market_state = _normalize_market_state(info.get("marketState"))

        # Build response
        price_data: Dict[str, Any] = {
            "ticker": ticker_upper,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": _safe_int(info.get("regularMarketVolume") or info.get("volume")),
            "high": round(_safe_float(info.get("regularMarketDayHigh") or info.get("dayHigh")), 2),
            "low": round(_safe_float(info.get("regularMarketDayLow") or info.get("dayLow")), 2),
            "open": round(_safe_float(info.get("regularMarketOpen") or info.get("open")), 2),
            "previous_close": round(previous_close, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_state": market_state,
        }

        # Cache the result
        cache.set(cache_key, price_data, expire=settings.PRICE_CACHE_TTL)
        logger.debug(f"Cached price data for {ticker_upper} with TTL={settings.PRICE_CACHE_TTL}s")

        return price_data

    except TickerNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker_upper}: {e}")
        raise DataFetchError(f"Failed to fetch price data for '{ticker_upper}': {str(e)}")


async def get_historical_data(ticker: str, period: PeriodType = "1y") -> List[Dict[str, Any]]:
    """
    Get historical OHLCV data for a stock ticker.

    Uses caching with TTL based on the period requested:
    - Short periods (1mo, 3mo): 30 seconds
    - Medium periods (6mo, 1y): 5 minutes
    - Long periods (5y): 1 hour

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT").
        period: Time period for historical data.
            Valid options: "1mo", "3mo", "6mo", "1y", "5y"

    Returns:
        List of dictionaries, each containing:
            - time: int (Unix timestamp in seconds)
            - open: float
            - high: float
            - low: float
            - close: float
            - volume: int

    Raises:
        ValueError: If the period is invalid.
        TickerNotFoundError: If the ticker is invalid or not found.
        DataFetchError: If there's an error fetching data from yfinance.
    """
    # Validate period
    if period not in VALID_PERIODS:
        raise ValueError(
            f"Invalid period '{period}'. Valid options are: {', '.join(VALID_PERIODS)}"
        )

    ticker_upper = ticker.upper().strip()
    cache_key = f"history:{ticker_upper}:{period}"

    # Determine cache TTL based on period
    cache_ttl_map = {
        "1mo": 30,      # 30 seconds for recent data
        "3mo": 30,      # 30 seconds
        "6mo": 300,     # 5 minutes
        "1y": 300,      # 5 minutes
        "5y": 3600,     # 1 hour for historical data
    }
    cache_ttl = cache_ttl_map.get(period, 300)

    # Check cache first
    cache = _get_cache()
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.debug(f"Cache hit for {ticker_upper} historical data ({period})")
        return cached_data

    logger.info(f"Fetching historical data for {ticker_upper} (period={period})")

    try:
        # Determine interval based on period for optimal granularity
        interval_map = {
            "1mo": "1d",    # Daily for 1 month
            "3mo": "1d",    # Daily for 3 months
            "6mo": "1d",    # Daily for 6 months
            "1y": "1d",     # Daily for 1 year
            "5y": "1wk",    # Weekly for 5 years
        }
        interval = interval_map.get(period, "1d")

        # Fetch historical data (run in thread pool to avoid blocking)
        def fetch_history():
            stock = yf.Ticker(ticker_upper)
            return stock.history(period=period, interval=interval), stock

        try:
            hist, stock = await asyncio.wait_for(
                asyncio.to_thread(fetch_history),
                timeout=YFINANCE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise DataFetchError(
                f"Timeout fetching historical data for '{ticker_upper}' after {YFINANCE_TIMEOUT}s"
            )

        if hist.empty:
            # Check if ticker exists (run in thread pool)
            def fetch_info():
                return stock.info

            try:
                info = await asyncio.wait_for(
                    asyncio.to_thread(fetch_info),
                    timeout=YFINANCE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                raise DataFetchError(
                    f"Timeout validating ticker '{ticker_upper}' after {YFINANCE_TIMEOUT}s"
                )
            if not info.get("shortName") and not info.get("symbol"):
                raise TickerNotFoundError(
                    f"Ticker '{ticker_upper}' not found or has no historical data"
                )
            # Return empty list if ticker exists but has no data for period
            return []

        # Convert to list of dicts with Unix timestamps
        historical_data: List[Dict[str, Any]] = []
        for index, row in hist.iterrows():
            # Convert pandas Timestamp to Unix timestamp (seconds)
            unix_timestamp = int(index.timestamp())

            data_point = {
                "time": unix_timestamp,
                "open": round(_safe_float(row.get("Open")), 2),
                "high": round(_safe_float(row.get("High")), 2),
                "low": round(_safe_float(row.get("Low")), 2),
                "close": round(_safe_float(row.get("Close")), 2),
                "volume": _safe_int(row.get("Volume")),
            }
            historical_data.append(data_point)

        # Cache the result
        cache.set(cache_key, historical_data, expire=cache_ttl)
        logger.debug(
            f"Cached historical data for {ticker_upper} ({period}) with TTL={cache_ttl}s"
        )

        return historical_data

    except TickerNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker_upper}: {e}")
        raise DataFetchError(
            f"Failed to fetch historical data for '{ticker_upper}': {str(e)}"
        )


def clear_price_cache(ticker: str | None = None) -> int:
    """
    Clear price cache entries.

    Args:
        ticker: Optional ticker to clear cache for.
            If None, clears all price cache entries.

    Returns:
        Number of cache entries cleared.
    """
    cache = _get_cache()
    cleared_count = 0

    if ticker:
        ticker_upper = ticker.upper().strip()
        # Clear specific ticker entries
        keys_to_clear = [
            f"price:{ticker_upper}",
        ]
        # Also clear all history entries for this ticker
        for period in VALID_PERIODS:
            keys_to_clear.append(f"history:{ticker_upper}:{period}")

        for key in keys_to_clear:
            if cache.delete(key):
                cleared_count += 1
    else:
        # Clear entire cache
        cleared_count = len(cache)
        cache.clear()

    logger.info(f"Cleared {cleared_count} cache entries")
    return cleared_count


async def is_market_open() -> Dict[str, Any]:
    """
    Check if the US stock market is currently open.

    Returns:
        Dictionary containing:
            - is_open: bool
            - market_state: str
            - timestamp: str (ISO format)
    """
    try:
        # Use SPY as a proxy for market status (run in thread pool to avoid blocking)
        def fetch_market_status():
            spy = yf.Ticker("SPY")
            return spy.info

        info = await asyncio.wait_for(
            asyncio.to_thread(fetch_market_status),
            timeout=YFINANCE_TIMEOUT,
        )
        market_state = _normalize_market_state(info.get("marketState"))

        return {
            "is_open": market_state == "REGULAR",
            "market_state": market_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except asyncio.TimeoutError:
        logger.warning(f"Timeout checking market status after {YFINANCE_TIMEOUT}s")
        return {
            "is_open": False,
            "market_state": "UNKNOWN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.warning(f"Failed to check market status: {e}")
        return {
            "is_open": False,
            "market_state": "UNKNOWN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
