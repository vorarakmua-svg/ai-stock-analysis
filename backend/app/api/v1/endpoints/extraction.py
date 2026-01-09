"""
API endpoints for AI-powered financial data extraction.

This module provides endpoints for extracting standardized valuation inputs
from raw stock JSON data using Google Gemini AI.

Endpoints:
    GET /{ticker}/extraction - Get standardized valuation input for a stock
    POST /{ticker}/extraction/refresh - Force refresh extraction (bypass cache)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.models.valuation_input import StandardizedValuationInput
from app.services.ai_extractor import (
    AIExtractor,
    DataNotFoundError,
    ExtractionError,
    GeminiAPIError,
    InvalidResponseError,
    get_ai_extractor,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{ticker}/extraction",
    response_model=StandardizedValuationInput,
    summary="Get standardized valuation input",
    description="""
    Extract and normalize financial data for a stock using AI.

    This endpoint returns a StandardizedValuationInput containing all the data
    needed for DCF and Graham valuations, extracted from raw JSON files using
    Google Gemini AI.

    The extraction process:
    1. Loads the stock's JSON file (~500-700KB)
    2. Truncates to essential sections (~15-20KB)
    3. Sends to Gemini for normalization and extraction
    4. Validates the response against the schema
    5. Caches the result for 7 days

    Cached results are returned immediately. Use the refresh parameter or
    POST /{ticker}/extraction/refresh to force a new extraction.
    """,
    responses={
        200: {
            "description": "Successfully extracted valuation input",
            "model": StandardizedValuationInput,
        },
        404: {
            "description": "Stock data not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Stock data file not found for INVALID"}
                }
            },
        },
        500: {
            "description": "Extraction failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to extract data: API error"}
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Gemini API unavailable. Please try again later."}
                }
            },
        },
    },
)
async def get_extraction(
    ticker: Annotated[
        str,
        Path(
            description="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)",
            min_length=1,
            max_length=10,
            examples=["AAPL", "MSFT", "GOOGL"],
        ),
    ],
    refresh: Annotated[
        bool,
        Query(
            description="Force refresh extraction (bypass cache)",
        ),
    ] = False,
    extractor: AIExtractor = Depends(get_ai_extractor),
) -> StandardizedValuationInput:
    """
    Get standardized valuation input for a stock.

    This endpoint extracts and normalizes financial data from the stock's
    JSON file using Gemini AI. Results are cached for 7 days.

    Args:
        ticker: Stock ticker symbol (case-insensitive)
        refresh: If True, bypass cache and force new extraction
        extractor: AI extractor service (injected)

    Returns:
        StandardizedValuationInput with extracted data

    Raises:
        HTTPException: 404 if stock not found, 500/503 on extraction failure
    """
    ticker = ticker.upper().strip()
    logger.info(
        "Extraction request for %s (refresh=%s)",
        ticker,
        refresh,
    )

    try:
        result = await extractor.extract_valuation_input(
            ticker=ticker,
            force_refresh=refresh,
        )

        logger.info(
            "Extraction successful for %s (confidence: %.2f)",
            ticker,
            result.data_confidence_score,
        )

        return result

    except DataNotFoundError as e:
        logger.warning("Stock data not found: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data file not found for {ticker}",
        ) from e

    except GeminiAPIError as e:
        logger.error("Gemini API error for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API unavailable. Please try again later.",
        ) from e

    except InvalidResponseError as e:
        logger.error("Invalid AI response for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI response. Please try again.",
        ) from e

    except ExtractionError as e:
        logger.error("Extraction error for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data extraction failed. Please try again later.",
        ) from e

    except Exception as e:
        logger.exception("Unexpected error during extraction for %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/{ticker}/extraction/refresh",
    response_model=StandardizedValuationInput,
    summary="Force refresh extraction",
    description="""
    Force a fresh extraction for a stock, bypassing the cache.

    Use this endpoint when:
    - Stock data has been updated and you need new extraction
    - You suspect the cached extraction has issues
    - You want to test extraction with updated AI prompts

    This operation may take 10-30 seconds due to AI processing time.
    """,
    responses={
        200: {
            "description": "Successfully refreshed extraction",
            "model": StandardizedValuationInput,
        },
        404: {"description": "Stock data not found"},
        503: {"description": "AI service unavailable"},
    },
)
async def refresh_extraction(
    ticker: Annotated[
        str,
        Path(
            description="Stock ticker symbol",
            min_length=1,
            max_length=10,
            examples=["AAPL", "MSFT", "GOOGL"],
        ),
    ],
    extractor: AIExtractor = Depends(get_ai_extractor),
) -> StandardizedValuationInput:
    """
    Force refresh extraction for a stock.

    This endpoint always bypasses the cache and performs a fresh extraction.

    Args:
        ticker: Stock ticker symbol (case-insensitive)
        extractor: AI extractor service (injected)

    Returns:
        StandardizedValuationInput with freshly extracted data

    Raises:
        HTTPException: 404 if stock not found, 500/503 on extraction failure
    """
    ticker = ticker.upper().strip()
    logger.info("Force refresh extraction request for %s", ticker)

    try:
        result = await extractor.extract_valuation_input(
            ticker=ticker,
            force_refresh=True,
        )

        logger.info(
            "Refresh extraction successful for %s (confidence: %.2f)",
            ticker,
            result.data_confidence_score,
        )

        return result

    except DataNotFoundError as e:
        logger.warning("Stock data not found: %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data file not found for {ticker}",
        ) from e

    except GeminiAPIError as e:
        logger.error("Gemini API error for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API unavailable. Please try again later.",
        ) from e

    except InvalidResponseError as e:
        logger.error("Invalid AI response for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI response. Please try again.",
        ) from e

    except ExtractionError as e:
        logger.error("Extraction error for %s: %s", ticker, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data extraction failed. Please try again later.",
        ) from e

    except Exception as e:
        logger.exception("Unexpected error during extraction for %s", ticker)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
