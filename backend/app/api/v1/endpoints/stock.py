"""
Stock detail API endpoint for retrieving full stock financial data.

Provides endpoint for:
- GET /stocks/{ticker} - Get complete stock JSON data
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.core.data_loader import (
    DataLoadError,
    get_available_tickers,
    load_stock_json,
)
from app.dependencies import TickerPath
from app.models.stock import StockDetailResponse

router = APIRouter()


@router.get(
    "/{ticker}",
    response_model=StockDetailResponse,
    summary="Get Stock Details",
    description="Retrieve complete financial data for a specific stock.",
    responses={
        200: {
            "description": "Stock data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "ticker": "AAPL",
                        "data": {
                            "company_info": {"name": "Apple Inc."},
                            "market_data": {"current_price": 262.36},
                        },
                    }
                }
            },
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock not found: XYZ"}
                }
            },
        },
    },
)
async def get_stock_detail(
    ticker: TickerPath,
) -> StockDetailResponse:
    """
    Get complete financial data for a specific stock.

    Args:
        ticker: Stock ticker symbol (case-insensitive).

    Returns:
        StockDetailResponse containing full stock JSON data.

    Raises:
        HTTPException 404: If the stock ticker is not found.
        HTTPException 500: If data cannot be loaded.
    """
    ticker_upper = ticker.upper()

    # Verify ticker exists
    try:
        available_tickers = get_available_tickers()
    except DataLoadError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if ticker_upper not in available_tickers:
        raise HTTPException(
            status_code=404,
            detail=f"Stock not found: {ticker_upper}",
        )

    # Load stock JSON data
    try:
        stock_data = load_stock_json(ticker_upper)
    except DataLoadError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StockDetailResponse(
        ticker=ticker_upper,
        data=stock_data,
    )


@router.get(
    "/{ticker}/summary",
    response_model=Dict[str, Any],
    summary="Get Stock Summary",
    description="Get a summarized view of key stock metrics.",
)
async def get_stock_summary(
    ticker: TickerPath,
) -> Dict[str, Any]:
    """
    Get summarized key metrics for a stock.

    Extracts the most important fields from the full stock data
    for a quick overview.

    Args:
        ticker: Stock ticker symbol (case-insensitive).

    Returns:
        Dictionary with key stock metrics.

    Raises:
        HTTPException 404: If the stock ticker is not found.
    """
    ticker_upper = ticker.upper()

    try:
        stock_data = load_stock_json(ticker_upper)
    except DataLoadError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Stock not found: {ticker_upper}")
        raise HTTPException(status_code=500, detail=str(e))

    # Extract key metrics for summary
    company_info = stock_data.get("company_info", {})
    market_data = stock_data.get("market_data", {})
    valuation = stock_data.get("valuation", {})
    calculated_metrics = stock_data.get("calculated_metrics", {})

    summary = {
        "ticker": ticker_upper,
        "company_name": company_info.get("name"),
        "sector": company_info.get("sector"),
        "industry": company_info.get("industry"),
        "current_price": market_data.get("current_price"),
        "market_cap": market_data.get("market_cap"),
        "pe_ratio": valuation.get("pe_trailing"),
        "forward_pe": valuation.get("pe_forward"),
        "eps": valuation.get("eps_trailing"),
        "dividend_yield": valuation.get("dividend_yield"),
        "beta": market_data.get("beta"),
        "fifty_two_week_high": market_data.get("52_week_high"),
        "fifty_two_week_low": market_data.get("52_week_low"),
        "enterprise_value": calculated_metrics.get("calc_ev"),
        "ev_to_ebitda": calculated_metrics.get("calc_ev_to_ebitda"),
        "free_cash_flow": calculated_metrics.get("calc_fcf"),
        "roic": calculated_metrics.get("calc_roic"),
        "collected_at": stock_data.get("collected_at"),
    }

    return summary
