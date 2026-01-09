"""
AI Analysis API endpoints.

This module provides endpoints for generating and retrieving
Warren Buffett-style investment analysis memos.

Endpoints:
- GET /{ticker}/analysis - Get AI-generated investment analysis
- POST /{ticker}/analysis/refresh - Force refresh analysis

The analysis combines quantitative valuation results with
qualitative business assessment to produce comprehensive
investment recommendations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.data_loader import get_available_tickers

from app.models.analysis import WarrenBuffettAnalysis
from app.services.ai_analyst import (
    AIAnalyst,
    AnalysisError,
    GeminiAnalysisError,
    InvalidAnalysisError,
    ValuationNotFoundError,
    get_ai_analyst,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiter instance for this router
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/{ticker}/analysis",
    response_model=WarrenBuffettAnalysis,
    summary="Get AI Investment Analysis",
    description="""
    Get Warren Buffett-style AI-generated investment analysis for a stock.

    This endpoint returns a comprehensive investment memo that includes:
    - Executive summary with investment thesis
    - Business quality assessment (moats, management, earnings power)
    - Financial health evaluation
    - Valuation summary with intrinsic value assessment
    - Key investment considerations (positives, concerns, risks, catalysts)
    - Final verdict with rating and conviction level

    **Process:**
    1. Retrieves or computes stock valuation
    2. Checks cache for existing analysis (7-day TTL)
    3. If not cached, generates new analysis using AI
    4. Returns the Warren Buffett-style investment memo

    **Rate Limiting:**
    Analysis generation is rate-limited to prevent API abuse.
    Cached results are returned instantly when available.

    **Note:** First-time analysis generation may take 15-30 seconds.
    """,
    responses={
        200: {
            "description": "Investment analysis generated successfully",
            "model": WarrenBuffettAnalysis,
        },
        404: {
            "description": "Stock not found or valuation unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock not found: INVALID"}
                }
            },
        },
        500: {
            "description": "Analysis generation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to generate analysis: API error"}
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "AI service temporarily unavailable"}
                }
            },
        },
    },
)
@limiter.limit("10/minute")
async def get_analysis(
    request: Request,
    ticker: str = Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9\-\.]+$",
        examples=["AAPL", "NVDA", "BRK-B"],
    ),
    force_refresh: bool = Query(
        default=False,
        description="Force regeneration of analysis, bypassing cache",
    ),
    analyst: AIAnalyst = Depends(get_ai_analyst),
) -> WarrenBuffettAnalysis:
    """
    Get Warren Buffett-style investment analysis for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        force_refresh: If True, regenerate analysis ignoring cache
        analyst: Injected AIAnalyst instance

    Returns:
        WarrenBuffettAnalysis containing the complete investment memo

    Raises:
        HTTPException: 404 if stock not found, 500 if generation fails,
                      503 if AI service unavailable
    """
    ticker = ticker.upper().strip()

    # Validate ticker exists
    available_tickers = get_available_tickers()
    if ticker not in available_tickers:
        logger.warning("Analysis requested for unknown ticker: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock not found: {ticker}",
        )

    try:
        logger.info(
            "Analysis request for %s (force_refresh=%s)",
            ticker,
            force_refresh,
        )

        analysis = await analyst.generate_analysis(
            ticker,
            force_refresh=force_refresh,
        )

        return analysis

    except ValuationNotFoundError as e:
        logger.error("Valuation not found for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Valuation data not available for {ticker}: {str(e)}",
        )

    except GeminiAnalysisError as e:
        logger.error("Gemini API error for %s analysis: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {str(e)}",
        )

    except InvalidAnalysisError as e:
        logger.error("Invalid analysis response for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse analysis response: {str(e)}",
        )

    except AnalysisError as e:
        logger.error("Analysis error for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis generation failed: {str(e)}",
        )

    except Exception as e:
        logger.exception("Unexpected error generating analysis for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/{ticker}/analysis/refresh",
    response_model=WarrenBuffettAnalysis,
    summary="Force Refresh AI Analysis",
    description="""
    Force regeneration of investment analysis for a stock.

    This endpoint bypasses all caches (valuation and analysis) and
    regenerates the complete analysis pipeline:
    1. Refresh AI data extraction
    2. Recalculate valuation
    3. Generate new AI analysis

    **Use Cases:**
    - After significant company news or events
    - When underlying data has been updated
    - When previous analysis may be stale

    **Warning:** This is a resource-intensive operation that makes
    multiple AI API calls. Use sparingly.

    **Estimated Time:** 30-60 seconds for complete refresh
    """,
    responses={
        200: {
            "description": "Analysis refreshed successfully",
            "model": WarrenBuffettAnalysis,
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock not found: INVALID"}
                }
            },
        },
        500: {
            "description": "Refresh failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to refresh analysis"}
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "AI service temporarily unavailable"}
                }
            },
        },
    },
)
@limiter.limit("3/minute")
async def refresh_analysis(
    request: Request,
    ticker: str = Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9\-\.]+$",
        examples=["AAPL", "NVDA", "BRK-B"],
    ),
    analyst: AIAnalyst = Depends(get_ai_analyst),
) -> WarrenBuffettAnalysis:
    """
    Force refresh investment analysis for a stock.

    Regenerates the complete analysis by:
    1. Invalidating cached data extraction
    2. Recalculating valuation
    3. Generating new AI analysis

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        analyst: Injected AIAnalyst instance

    Returns:
        WarrenBuffettAnalysis containing the freshly generated memo

    Raises:
        HTTPException: 404 if stock not found, 500 if refresh fails,
                      503 if AI service unavailable
    """
    ticker = ticker.upper().strip()

    # Validate ticker exists
    available_tickers = get_available_tickers()
    if ticker not in available_tickers:
        logger.warning("Analysis refresh requested for unknown ticker: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock not found: {ticker}",
        )

    try:
        logger.info("Forcing analysis refresh for %s", ticker)

        # Invalidate analysis cache first
        analyst.cache.invalidate(ticker)

        # Generate with force_refresh=True to also refresh valuation
        analysis = await analyst.generate_analysis(
            ticker,
            force_refresh=True,
        )

        logger.info(
            "Analysis refresh complete for %s: rating=%s",
            ticker,
            analysis.investment_rating.value,
        )

        return analysis

    except ValuationNotFoundError as e:
        logger.error("Valuation not found during refresh for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Valuation data not available for {ticker}: {str(e)}",
        )

    except GeminiAnalysisError as e:
        logger.error("Gemini API error during refresh for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {str(e)}",
        )

    except InvalidAnalysisError as e:
        logger.error("Invalid analysis response during refresh for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse analysis response: {str(e)}",
        )

    except AnalysisError as e:
        logger.error("Analysis error during refresh for %s: %s", ticker, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis refresh failed: {str(e)}",
        )

    except Exception as e:
        logger.exception(
            "Unexpected error during analysis refresh for %s: %s",
            ticker,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "/{ticker}/analysis/cached",
    summary="Get Cached Analysis Only",
    description="""
    Get cached investment analysis without triggering generation.

    This endpoint only returns analysis if it exists in cache.
    If no cached analysis is available, returns 204 No Content.

    **Use Cases:**
    - Quick check if analysis is available
    - Avoiding expensive regeneration
    - Loading previously generated analyses

    **Note:** Returns 204 (not 404) when analysis is not cached.
    """,
    responses={
        200: {
            "description": "Cached analysis found",
            "model": WarrenBuffettAnalysis,
        },
        204: {
            "description": "No cached analysis available",
        },
        404: {
            "description": "Stock not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock not found: INVALID"}
                }
            },
        },
    },
    response_model=WarrenBuffettAnalysis,
    response_model_exclude_none=True,
)
async def get_cached_analysis(
    ticker: str = Path(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9\-\.]+$",
        examples=["AAPL", "NVDA", "BRK-B"],
    ),
    analyst: AIAnalyst = Depends(get_ai_analyst),
) -> WarrenBuffettAnalysis | Response:
    """
    Get cached analysis only, without triggering generation.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        analyst: Injected AIAnalyst instance

    Returns:
        WarrenBuffettAnalysis if cached, 204 Response if not available

    Raises:
        HTTPException: 404 if stock ticker is not recognized
    """
    ticker = ticker.upper().strip()

    # Validate ticker exists
    available_tickers = get_available_tickers()
    if ticker not in available_tickers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock not found: {ticker}",
        )

    try:
        cached = await analyst.get_cached_analysis(ticker)

        if cached is not None:
            logger.debug("Returning cached analysis for %s", ticker)
            return cached

        logger.debug("No cached analysis for %s", ticker)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.warning("Error checking cached analysis for %s: %s", ticker, e)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
