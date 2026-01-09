"""
Valuation API endpoints for stock intrinsic value calculations.

This module provides endpoints for:
- GET /{ticker}/valuation - Get complete valuation (cached)
- POST /{ticker}/valuation/refresh - Force refresh valuation

The valuation combines:
- DCF (Discounted Cash Flow) with 3 scenarios
- Graham Number calculation
- Graham Defensive Screen (7 criteria)
- Composite intrinsic value (60% DCF + 40% Graham)

Architecture Notes:
- AI layer (Gemini) handles data extraction only
- All calculations are performed in Python (ValuationEngine)
- Results are cached for 24 hours (VALUATION_CACHE_TTL)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter for valuation endpoints (expensive AI operations)
limiter = Limiter(key_func=get_remote_address)

from app.models.valuation_output import ValuationResult
from app.models.flexible_input import FlexibleValuationInput
from app.services.ai_extractor import (
    AIExtractor,
    APIKeyNotConfiguredError,
    DataNotFoundError,
    ExtractionError,
    GeminiAPIError,
    get_ai_extractor,
)
from app.services.valuation_engine import (
    ValuationEngine,
    ValuationError,
    get_valuation_engine,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Type alias for path parameter
TickerPath = Annotated[
    str,
    Path(
        ...,
        description="Stock ticker symbol (e.g., AAPL, MSFT)",
        min_length=1,
        max_length=10,
        examples=["AAPL", "MSFT", "GOOGL"],
    ),
]


@router.get(
    "/{ticker}/valuation",
    response_model=ValuationResult,
    summary="Get stock valuation",
    description="""
    Get complete valuation analysis for a stock.

    The valuation includes:
    - **DCF Analysis**: Discounted Cash Flow with conservative, base case, and optimistic scenarios
    - **Graham Number**: Benjamin Graham's intrinsic value formula
    - **Graham Defensive Screen**: 7 criteria for defensive investors
    - **Composite Value**: Weighted average (60% DCF + 40% Graham)
    - **Investment Verdict**: Based on upside/downside potential

    Results are cached for 24 hours. Use the POST endpoint to force a refresh.

    **Note**: First request for a stock may take 10-30 seconds as AI extracts and normalizes financial data.
    """,
    responses={
        200: {
            "description": "Valuation calculated successfully",
            "model": ValuationResult,
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock data not found for ticker: XYZ"}
                }
            },
        },
        500: {
            "description": "Valuation calculation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to calculate valuation: internal error"}
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "AI extraction service is temporarily unavailable"}
                }
            },
        },
    },
)
@limiter.limit("10/minute")
async def get_valuation(
    request: Request,
    ticker: TickerPath,
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> ValuationResult:
    """
    Get complete valuation for a stock ticker.

    This endpoint returns a comprehensive valuation analysis including
    DCF calculations, Graham Number, and defensive screen criteria.
    Results are cached for 24 hours.

    Args:
        ticker: Stock ticker symbol (case-insensitive)
        engine: Valuation engine dependency

    Returns:
        ValuationResult with complete analysis

    Raises:
        HTTPException: 404 if stock not found, 500 on calculation error, 503 on AI service error
    """
    ticker = ticker.upper().strip()
    logger.info("GET valuation request for %s", ticker)

    try:
        result = await engine.calculate_valuation(ticker, force_refresh=False)
        logger.info(
            "Valuation returned for %s: $%.2f composite IV, %s verdict",
            ticker,
            result.composite_intrinsic_value,
            result.verdict.value,
        )
        return result

    except APIKeyNotConfiguredError as e:
        logger.warning("API key not configured for valuation: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    except DataNotFoundError as e:
        logger.warning("Stock not found: %s - %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found for ticker: {ticker}",
        )

    except GeminiAPIError as e:
        logger.error("AI service error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI extraction service is temporarily unavailable. Please try again later.",
        )

    except ExtractionError as e:
        logger.error("Extraction error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract financial data for {ticker}: {str(e)}",
        )

    except ValuationError as e:
        logger.error("Valuation error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate valuation for {ticker}: {str(e)}",
        )

    except Exception as e:
        logger.exception("Unexpected error in valuation for %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post(
    "/{ticker}/valuation/refresh",
    response_model=ValuationResult,
    summary="Force refresh stock valuation",
    description="""
    Force a fresh valuation calculation, bypassing the cache.

    Use this endpoint when:
    - Stock data has been updated
    - You want to recalculate with latest market data
    - Cached valuation seems stale

    **Warning**: This triggers a new AI extraction which may take 10-30 seconds
    and consumes API quota.
    """,
    responses={
        200: {
            "description": "Valuation refreshed successfully",
            "model": ValuationResult,
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock data not found for ticker: XYZ"}
                }
            },
        },
        500: {
            "description": "Valuation calculation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to calculate valuation: internal error"}
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "AI extraction service is temporarily unavailable"}
                }
            },
        },
    },
)
@limiter.limit("5/minute")
async def refresh_valuation(
    request: Request,
    ticker: TickerPath,
    engine: ValuationEngine = Depends(get_valuation_engine),
) -> ValuationResult:
    """
    Force refresh valuation for a stock ticker.

    Bypasses cache and triggers a new AI extraction and valuation calculation.
    Use sparingly as this consumes AI API quota.

    Args:
        ticker: Stock ticker symbol (case-insensitive)
        engine: Valuation engine dependency

    Returns:
        ValuationResult with fresh analysis

    Raises:
        HTTPException: 404 if stock not found, 500 on calculation error, 503 on AI service error
    """
    ticker = ticker.upper().strip()
    logger.info("POST valuation refresh request for %s", ticker)

    try:
        result = await engine.calculate_valuation(ticker, force_refresh=True)
        logger.info(
            "Valuation refreshed for %s: $%.2f composite IV, %s verdict",
            ticker,
            result.composite_intrinsic_value,
            result.verdict.value,
        )
        return result

    except APIKeyNotConfiguredError as e:
        logger.warning("API key not configured for valuation refresh: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    except DataNotFoundError as e:
        logger.warning("Stock not found: %s - %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found for ticker: {ticker}",
        )

    except GeminiAPIError as e:
        logger.error("AI service error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI extraction service is temporarily unavailable. Please try again later.",
        )

    except ExtractionError as e:
        logger.error("Extraction error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract financial data for {ticker}: {str(e)}",
        )

    except ValuationError as e:
        logger.error("Valuation error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate valuation for {ticker}: {str(e)}",
        )

    except Exception as e:
        logger.exception("Unexpected error in valuation refresh for %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/{ticker}/extraction/flexible",
    response_model=FlexibleValuationInput,
    summary="Test flexible AI extraction",
    description="""
    Test the flexible extraction approach where AI extracts ALL available data.

    This endpoint lets the AI decide what data to extract without forcing
    a rigid schema. Useful for debugging and seeing what data is available.

    **Note**: This is a test endpoint and may take 10-30 seconds.
    """,
)
async def get_flexible_extraction(
    ticker: TickerPath,
    extractor: AIExtractor = Depends(get_ai_extractor),
) -> FlexibleValuationInput:
    """
    Get flexible extraction for a stock ticker.

    This lets the AI extract ALL available financial data without
    forcing a rigid schema. The AI decides what to extract.
    """
    ticker = ticker.upper().strip()
    logger.info("GET flexible extraction request for %s", ticker)

    try:
        result = await extractor.extract_flexible(ticker, force_refresh=True)
        logger.info(
            "Flexible extraction returned for %s: confidence=%.2f",
            ticker,
            result.data_confidence_score,
        )
        return result

    except APIKeyNotConfiguredError as e:
        logger.warning("API key not configured: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    except DataNotFoundError as e:
        logger.warning("Stock not found: %s - %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found for ticker: {ticker}",
        )

    except GeminiAPIError as e:
        logger.error("AI service error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI extraction service is temporarily unavailable.",
        )

    except ExtractionError as e:
        logger.error("Extraction error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract data for {ticker}: {str(e)}",
        )

    except Exception as e:
        logger.exception("Unexpected error in flexible extraction for %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
