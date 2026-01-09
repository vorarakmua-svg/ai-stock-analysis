"""
Screener API endpoints for listing and filtering stocks.

Provides endpoints for:
- GET /stocks - List all stocks with optional filtering/sorting
- GET /stocks/metadata - Get available columns, sectors, industries
"""

import logging
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

from app.core.data_loader import (
    DataLoadError,
    get_column_names,
    get_unique_industries,
    get_unique_sectors,
    load_summary_csv,
    get_available_tickers,
)
from app.models.stock import (
    StockListResponse,
    StockMetadataResponse,
    StockSummary,
)

router = APIRouter()


class SortOrder(str, Enum):
    """Sort order enumeration."""

    asc = "asc"
    desc = "desc"


@router.get(
    "",
    response_model=StockListResponse,
    summary="List All Stocks",
    description="Retrieve all stocks with optional filtering and sorting.",
)
async def get_stocks(
    sort_by: Optional[str] = Query(
        None,
        description="Column name to sort by (e.g., 'market_cap', 'pe_trailing')",
    ),
    sort_order: SortOrder = Query(
        SortOrder.desc,
        description="Sort order: 'asc' or 'desc'",
    ),
    sector: Optional[str] = Query(
        None,
        description="Filter by sector (e.g., 'Technology')",
    ),
    industry: Optional[str] = Query(
        None,
        description="Filter by industry (e.g., 'Semiconductors')",
    ),
    search: Optional[str] = Query(
        None,
        description="Search ticker or company name (case-insensitive)",
    ),
    min_market_cap: Optional[float] = Query(
        None,
        description="Minimum market cap filter",
        ge=0,
    ),
    max_market_cap: Optional[float] = Query(
        None,
        description="Maximum market cap filter",
        ge=0,
    ),
    min_pe: Optional[float] = Query(
        None,
        description="Minimum trailing P/E filter",
    ),
    max_pe: Optional[float] = Query(
        None,
        description="Maximum trailing P/E filter",
    ),
) -> StockListResponse:
    """
    List all stocks with optional filtering and sorting.

    Args:
        sort_by: Column name to sort by.
        sort_order: Sort direction ('asc' or 'desc').
        sector: Filter by sector.
        industry: Filter by industry.
        search: Search term for ticker or company name.
        min_market_cap: Minimum market cap filter.
        max_market_cap: Maximum market cap filter.
        min_pe: Minimum P/E ratio filter.
        max_pe: Maximum P/E ratio filter.

    Returns:
        StockListResponse with filtered/sorted stocks.

    Raises:
        HTTPException: If data cannot be loaded or invalid sort column.
    """
    try:
        raw_stocks = load_summary_csv()
    except DataLoadError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Convert to StockSummary models for validation
    stocks: List[StockSummary] = []
    skipped_count = 0
    for raw in raw_stocks:
        try:
            stock = StockSummary.model_validate(raw)
            stocks.append(stock)
        except Exception as e:
            # Log validation errors for debugging
            ticker = raw.get("ticker", "unknown") if isinstance(raw, dict) else "unknown"
            logger.warning("Skipping invalid stock row (ticker=%s): %s", ticker, str(e)[:100])
            skipped_count += 1
            continue

    if skipped_count > 0:
        logger.info("Loaded %d stocks, skipped %d invalid rows", len(stocks), skipped_count)

    # Apply filters
    filtered_stocks = stocks

    # Sector filter
    if sector:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.sector and s.sector.lower() == sector.lower()
        ]

    # Industry filter
    if industry:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.industry and s.industry.lower() == industry.lower()
        ]

    # Search filter (ticker or company name)
    if search:
        search_lower = search.lower()
        filtered_stocks = [
            s for s in filtered_stocks
            if (
                search_lower in s.ticker.lower()
                or (s.company_name and search_lower in s.company_name.lower())
            )
        ]

    # Market cap range filter
    if min_market_cap is not None:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.market_cap is not None and s.market_cap >= min_market_cap
        ]

    if max_market_cap is not None:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.market_cap is not None and s.market_cap <= max_market_cap
        ]

    # P/E ratio range filter
    if min_pe is not None:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.pe_trailing is not None and s.pe_trailing >= min_pe
        ]

    if max_pe is not None:
        filtered_stocks = [
            s for s in filtered_stocks
            if s.pe_trailing is not None and s.pe_trailing <= max_pe
        ]

    # Apply sorting
    if sort_by:
        # Validate sort column exists
        valid_columns = get_column_names()
        # Map aliased field names to actual CSV column names
        column_mapping = {
            "fifty_two_week_high": "52_week_high",
            "fifty_two_week_low": "52_week_low",
        }
        actual_sort_by = column_mapping.get(sort_by, sort_by)

        if actual_sort_by not in valid_columns and sort_by not in valid_columns:
            # Also allow Pydantic field names
            field_names = [f for f in StockSummary.model_fields.keys()]
            if sort_by not in field_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sort column: {sort_by}. Valid columns: {valid_columns[:10]}...",
                )

        # Sort using the field name (not alias)
        def get_sort_key(stock: StockSummary):
            value = getattr(stock, sort_by, None)
            if value is None:
                # Put None values at the end for desc, beginning for asc
                return (1, 0) if sort_order == SortOrder.desc else (0, 0)
            return (0, value)

        reverse = sort_order == SortOrder.desc
        filtered_stocks = sorted(filtered_stocks, key=get_sort_key, reverse=reverse)

    # Get column names for response
    try:
        columns = get_column_names()
    except DataLoadError:
        columns = list(StockSummary.model_fields.keys())

    return StockListResponse(
        stocks=filtered_stocks,
        total=len(filtered_stocks),
        columns=columns,
    )


@router.get(
    "/metadata",
    response_model=StockMetadataResponse,
    summary="Get Stock Metadata",
    description="Get available columns, sectors, and industries for filter dropdowns.",
)
async def get_stock_metadata() -> StockMetadataResponse:
    """
    Get metadata for building filter dropdowns and column selectors.

    Returns:
        StockMetadataResponse with columns, sectors, industries, and tickers.

    Raises:
        HTTPException: If data cannot be loaded.
    """
    try:
        columns = get_column_names()
        sectors = get_unique_sectors()
        industries = get_unique_industries()
        tickers = get_available_tickers()
    except DataLoadError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StockMetadataResponse(
        columns=columns,
        sectors=sectors,
        industries=industries,
        tickers=tickers,
    )
