"""
Real-time stock data API endpoints.

Provides endpoints for:
- GET /{ticker}/price - Get real-time price data
- GET /{ticker}/history - Get historical OHLCV data
"""

import logging
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from app.services.realtime_service import (
    DataFetchError,
    TickerNotFoundError,
    get_historical_data,
    get_realtime_price,
    is_market_open,
    VALID_PERIODS,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class PriceResponse(BaseModel):
    """Response model for real-time price data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "price": 178.50,
                "change": 2.35,
                "change_percent": 1.33,
                "volume": 52436789,
                "high": 179.25,
                "low": 176.80,
                "open": 177.10,
                "previous_close": 176.15,
                "timestamp": "2026-01-07T15:30:00+00:00",
                "market_state": "REGULAR",
            }
        }
    )

    ticker: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., description="Current or latest price")
    change: float = Field(..., description="Absolute price change from previous close")
    change_percent: float = Field(..., description="Percentage change from previous close")
    volume: int = Field(..., description="Trading volume")
    high: float = Field(..., description="Day's high price")
    low: float = Field(..., description="Day's low price")
    open: float = Field(..., description="Day's opening price")
    previous_close: float = Field(..., description="Previous day's closing price")
    timestamp: str = Field(..., description="Data timestamp in ISO format")
    market_state: str = Field(
        ...,
        description="Market state: PRE, REGULAR, POST, or CLOSED"
    )


class OHLCVDataPoint(BaseModel):
    """Single OHLCV data point for historical data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time": 1704672000,
                "open": 175.50,
                "high": 178.25,
                "low": 174.80,
                "close": 177.90,
                "volume": 48523000,
            }
        }
    )

    time: int = Field(..., description="Unix timestamp in seconds")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")


class MarketStatusResponse(BaseModel):
    """Response model for market status check."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_open": True,
                "market_state": "REGULAR",
                "timestamp": "2026-01-07T15:30:00+00:00",
            }
        }
    )

    is_open: bool = Field(..., description="Whether the market is currently open")
    market_state: str = Field(..., description="Current market state")
    timestamp: str = Field(..., description="Check timestamp in ISO format")


# Type for period parameter
PeriodType = Literal["1mo", "3mo", "6mo", "1y", "5y"]


@router.get(
    "/{ticker}/price",
    response_model=PriceResponse,
    summary="Get Real-Time Price",
    description="Retrieve real-time price data for a stock. Data is cached for 30 seconds.",
    responses={
        200: {
            "description": "Price data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "ticker": "AAPL",
                        "price": 178.50,
                        "change": 2.35,
                        "change_percent": 1.33,
                        "volume": 52436789,
                        "high": 179.25,
                        "low": 176.80,
                        "open": 177.10,
                        "previous_close": 176.15,
                        "timestamp": "2026-01-07T15:30:00+00:00",
                        "market_state": "REGULAR",
                    }
                }
            },
        },
        404: {
            "description": "Ticker not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Ticker 'XYZ' not found or has no market data"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to fetch price data: connection timeout"}
                }
            },
        },
    },
)
async def get_stock_price(
    ticker: str = Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')",
        min_length=1,
        max_length=10,
        examples=["AAPL", "NVDA", "MSFT", "GOOGL"],
    ),
) -> PriceResponse:
    """
    Get real-time price data for a specific stock.

    This endpoint returns the current or most recent price data including:
    - Current price and price changes
    - Day's high, low, and open prices
    - Trading volume
    - Market state (pre-market, regular, after-hours, closed)

    Data is cached for 30 seconds to balance freshness with API rate limits.

    Args:
        ticker: Stock ticker symbol (case-insensitive).

    Returns:
        PriceResponse containing current price data.

    Raises:
        HTTPException 404: If the ticker is not found.
        HTTPException 500: If there's an error fetching data.
    """
    try:
        price_data = await get_realtime_price(ticker)
        return PriceResponse(**price_data)

    except TickerNotFoundError as e:
        logger.warning("Ticker not found: %s", ticker)
        raise HTTPException(status_code=404, detail=str(e))

    except DataFetchError as e:
        logger.error("Data fetch error for %s: %s", ticker, e)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception("Unexpected error fetching price for %s", ticker)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching price data"
        )


@router.get(
    "/{ticker}/history",
    response_model=List[OHLCVDataPoint],
    summary="Get Historical OHLCV Data",
    description="Retrieve historical OHLCV (Open, High, Low, Close, Volume) data for a stock.",
    responses={
        200: {
            "description": "Historical data retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "time": 1704672000,
                            "open": 175.50,
                            "high": 178.25,
                            "low": 174.80,
                            "close": 177.90,
                            "volume": 48523000,
                        },
                        {
                            "time": 1704758400,
                            "open": 177.90,
                            "high": 179.50,
                            "low": 177.20,
                            "close": 178.80,
                            "volume": 42156000,
                        },
                    ]
                }
            },
        },
        400: {
            "description": "Invalid period parameter",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid period '2y'. Valid options are: 1mo, 3mo, 6mo, 1y, 5y"
                    }
                }
            },
        },
        404: {
            "description": "Ticker not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Ticker 'XYZ' not found or has no historical data"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to fetch historical data: connection timeout"}
                }
            },
        },
    },
)
async def get_stock_history(
    ticker: str = Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')",
        min_length=1,
        max_length=10,
        examples=["AAPL", "NVDA", "MSFT", "GOOGL"],
    ),
    period: PeriodType = Query(
        default="1y",
        description="Time period for historical data",
        examples=["1mo", "3mo", "6mo", "1y", "5y"],
    ),
) -> List[OHLCVDataPoint]:
    """
    Get historical OHLCV data for a specific stock.

    This endpoint returns historical price data suitable for charting:
    - Daily data for periods up to 1 year
    - Weekly data for 5-year period

    Data is cached with TTL based on the period:
    - 1mo, 3mo: 30 seconds
    - 6mo, 1y: 5 minutes
    - 5y: 1 hour

    Args:
        ticker: Stock ticker symbol (case-insensitive).
        period: Time period for historical data.
            Options: "1mo", "3mo", "6mo", "1y", "5y"

    Returns:
        List of OHLCVDataPoint objects with historical price data.

    Raises:
        HTTPException 400: If the period is invalid.
        HTTPException 404: If the ticker is not found.
        HTTPException 500: If there's an error fetching data.
    """
    try:
        historical_data = await get_historical_data(ticker, period)
        return [OHLCVDataPoint(**point) for point in historical_data]

    except ValueError as e:
        logger.warning("Invalid period for %s: %s", ticker, period)
        raise HTTPException(status_code=400, detail=str(e))

    except TickerNotFoundError as e:
        logger.warning("Ticker not found: %s", ticker)
        raise HTTPException(status_code=404, detail=str(e))

    except DataFetchError as e:
        logger.error("Data fetch error for %s: %s", ticker, e)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception("Unexpected error fetching history for %s", ticker)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching historical data"
        )


@router.get(
    "/market/status",
    response_model=MarketStatusResponse,
    summary="Get Market Status",
    description="Check if the US stock market is currently open.",
    responses={
        200: {
            "description": "Market status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "is_open": True,
                        "market_state": "REGULAR",
                        "timestamp": "2026-01-07T15:30:00+00:00",
                    }
                }
            },
        },
    },
)
async def get_market_status() -> MarketStatusResponse:
    """
    Check the current US stock market status.

    Returns the current market state:
    - PRE: Pre-market trading (4:00 AM - 9:30 AM ET)
    - REGULAR: Regular trading hours (9:30 AM - 4:00 PM ET)
    - POST: After-hours trading (4:00 PM - 8:00 PM ET)
    - CLOSED: Market is closed

    Returns:
        MarketStatusResponse with current market state.
    """
    status = await is_market_open()
    return MarketStatusResponse(**status)
