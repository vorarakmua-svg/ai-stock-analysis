"""
AI-powered financial data extraction service using Google Gemini.

This module provides the AIExtractor class that uses Gemini Pro to extract
and normalize financial data from raw stock JSON files into the
StandardizedValuationInput schema.

Architecture Notes:
- AI Layer handles: Data extraction, normalization, field mapping, TTM calculations
- AI Layer does NOT handle: Valuation formulas (DCF, WACC, Graham Number)
- All mathematical calculations are performed in Python (valuation_engine.py)

Rate Limiting:
- Gemini API: Max 60 requests/minute for free tier
- Implemented with simple time-based throttling
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import google.generativeai as genai

from app.config import get_settings
from app.core.cache_manager import ExtractionCache, get_extraction_cache
from app.core.data_loader import load_stock_json
from app.models.valuation_input import StandardizedValuationInput
from app.models.flexible_input import FlexibleValuationInput
from app.prompts.extraction_prompt import SYSTEM_PROMPT, build_user_prompt
from app.prompts.extraction_prompt_v2 import (
    FLEXIBLE_SYSTEM_PROMPT,
    build_flexible_prompt,
)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class GeminiAPIError(ExtractionError):
    """Exception raised when Gemini API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class DataNotFoundError(ExtractionError):
    """Exception raised when stock data file is not found."""

    pass


class InvalidResponseError(ExtractionError):
    """Exception raised when AI response cannot be parsed."""

    pass


class APIKeyNotConfiguredError(ExtractionError):
    """Exception raised when GOOGLE_API_KEY is not configured."""

    pass


class AIExtractor:
    """
    AI-powered financial data extractor using Google Gemini Pro.

    This class handles the extraction of standardized valuation inputs from
    raw stock JSON files. It manages API calls, rate limiting, caching,
    and response validation.

    Attributes:
        model: Gemini GenerativeModel instance
        cache: ExtractionCache for result caching
        last_request_time: Timestamp of last API call for rate limiting
        request_count: Number of requests in current minute window

    Example:
        extractor = AIExtractor()
        result = await extractor.extract_valuation_input("AAPL")
    """

    # Rate limiting constants
    MAX_REQUESTS_PER_MINUTE = 60
    MIN_REQUEST_INTERVAL = 1.0  # Minimum seconds between requests

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # Base delay in seconds

    def __init__(
        self,
        cache: ExtractionCache | None = None,
    ) -> None:
        """
        Initialize the AI extractor.

        Args:
            cache: Optional ExtractionCache instance. If not provided,
                  uses the singleton cache from get_extraction_cache().

        Raises:
            ValueError: If GOOGLE_API_KEY is not configured.
        """
        settings = get_settings()

        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. Please set it in .env file."
            )

        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)

        # Initialize model with appropriate settings
        # Model options for extraction (choose based on needs):
        # - "gemini-2.0-flash": Fast, cheap, good for structured tasks (DEFAULT)
        # - "gemini-1.5-pro": More capable, better instruction following, slower
        # - "gemini-1.5-flash": Balance of speed and capability
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.0,  # Zero temperature for maximum consistency
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json",  # Force JSON output
            ),
        )

        # Initialize cache
        self.cache = cache or get_extraction_cache()

        # Rate limiting state
        self._last_request_time: float = 0.0
        self._request_count: int = 0
        self._window_start: float = time.time()
        self._rate_limit_lock: asyncio.Lock = asyncio.Lock()

        logger.info("AIExtractor initialized with Gemini model: gemini-2.0-flash")

    def truncate_json(self, stock_data: dict) -> dict:
        """
        Extract only the sections needed for AI extraction (~15-20KB).

        This reduces API token usage while preserving all necessary data
        for comprehensive extraction.

        Args:
            stock_data: Full stock JSON data (~500-700KB)

        Returns:
            Truncated dict containing only essential sections.

        Sections Preserved:
            - company_info: Company metadata (sector, industry, description)
            - market_data: Current price, market cap, beta
            - valuation: Pre-calculated valuation metrics
            - calculated_metrics: ROIC, margins, etc.
            - financials_annual: Last 10 years of SEC data
            - yahoo_financials.income_statement_quarterly: Last 4-8 quarters
            - yahoo_financials.balance_sheet: Most recent
            - yahoo_financials.cash_flow_statement_quarterly: Last 4-8 quarters
        """
        truncated = {
            "ticker": stock_data.get("ticker", ""),
            "company_name": stock_data.get("company_name", ""),
            "collected_at": stock_data.get("collected_at", ""),
        }

        # Company info (keep everything - it's small)
        if "company_info" in stock_data:
            company_info = stock_data["company_info"].copy()
            # Remove large nested arrays to save tokens
            company_info.pop("officers", None)
            truncated["company_info"] = company_info

        # Market data (keep all - essential for valuation)
        if "market_data" in stock_data:
            truncated["market_data"] = stock_data["market_data"]

        # Valuation section (keep all pre-calculated metrics)
        if "valuation" in stock_data:
            truncated["valuation"] = stock_data["valuation"]

        # Shareholders (only need shares outstanding)
        if "shareholders" in stock_data:
            shareholders = stock_data["shareholders"]
            truncated["shareholders"] = {
                "shares_outstanding": shareholders.get("shares_outstanding"),
                "float_shares": shareholders.get("float_shares"),
            }

        # Calculated metrics (keep current metrics, truncate historical)
        if "calculated_metrics" in stock_data:
            calc_metrics = stock_data["calculated_metrics"].copy()
            # Keep only last 5 years of historical for efficiency
            if "historical" in calc_metrics:
                historical = calc_metrics["historical"]
                # Get most recent 5 years
                sorted_years = sorted(historical.keys(), reverse=True)[:5]
                calc_metrics["historical"] = {
                    year: historical[year] for year in sorted_years
                }
            truncated["calculated_metrics"] = calc_metrics

        # Annual financials (keep last 10 years for CAGR calculations)
        if "financials_annual" in stock_data:
            annual = stock_data["financials_annual"]
            sorted_years = sorted(annual.keys(), reverse=True)[:10]
            truncated["financials_annual"] = {
                year: annual[year] for year in sorted_years
            }

        # Yahoo financials (quarterly data for TTM)
        if "yahoo_financials" in stock_data:
            yahoo = stock_data["yahoo_financials"]
            truncated["yahoo_financials"] = {}

            # Income statement - quarterly (last 8 quarters)
            if "income_statement_quarterly" in yahoo:
                quarterly_income = yahoo["income_statement_quarterly"]
                sorted_quarters = sorted(quarterly_income.keys(), reverse=True)[:8]
                truncated["yahoo_financials"]["income_statement_quarterly"] = {
                    q: quarterly_income[q] for q in sorted_quarters
                }

            # Income statement - annual (last 5 years)
            if "income_statement_annual" in yahoo:
                annual_income = yahoo["income_statement_annual"]
                sorted_years = sorted(annual_income.keys(), reverse=True)[:5]
                truncated["yahoo_financials"]["income_statement_annual"] = {
                    y: annual_income[y] for y in sorted_years
                }

            # Balance sheet - quarterly (last 4 quarters)
            if "balance_sheet_quarterly" in yahoo:
                quarterly_bs = yahoo["balance_sheet_quarterly"]
                sorted_quarters = sorted(quarterly_bs.keys(), reverse=True)[:4]
                truncated["yahoo_financials"]["balance_sheet_quarterly"] = {
                    q: quarterly_bs[q] for q in sorted_quarters
                }

            # Balance sheet - annual (last 5 years)
            if "balance_sheet_annual" in yahoo:
                annual_bs = yahoo["balance_sheet_annual"]
                sorted_years = sorted(annual_bs.keys(), reverse=True)[:5]
                truncated["yahoo_financials"]["balance_sheet_annual"] = {
                    y: annual_bs[y] for y in sorted_years
                }

            # Cash flow - quarterly (last 8 quarters)
            # Support both naming conventions: cash_flow_quarterly and cash_flow_statement_quarterly
            quarterly_cf_key = "cash_flow_quarterly" if "cash_flow_quarterly" in yahoo else "cash_flow_statement_quarterly"
            if quarterly_cf_key in yahoo:
                quarterly_cf = yahoo[quarterly_cf_key]
                sorted_quarters = sorted(quarterly_cf.keys(), reverse=True)[:8]
                truncated["yahoo_financials"]["cash_flow_statement_quarterly"] = {
                    q: quarterly_cf[q] for q in sorted_quarters
                }

            # Cash flow - annual (last 5 years)
            # Support both naming conventions: cash_flow_annual and cash_flow_statement_annual
            annual_cf_key = "cash_flow_annual" if "cash_flow_annual" in yahoo else "cash_flow_statement_annual"
            if annual_cf_key in yahoo:
                annual_cf = yahoo[annual_cf_key]
                sorted_years = sorted(annual_cf.keys(), reverse=True)[:5]
                truncated["yahoo_financials"]["cash_flow_statement_annual"] = {
                    y: annual_cf[y] for y in sorted_years
                }

        return truncated

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting for API calls.

        Ensures compliance with Gemini API limits (60 requests/minute).
        Uses a sliding window approach with minimum interval enforcement.
        Thread-safe using asyncio.Lock for concurrent coroutines.
        """
        async with self._rate_limit_lock:
            current_time = time.time()

            # Reset window if more than 60 seconds have passed
            if current_time - self._window_start >= 60:
                self._request_count = 0
                self._window_start = current_time

            # Check if we've hit the rate limit
            if self._request_count >= self.MAX_REQUESTS_PER_MINUTE:
                wait_time = 60 - (current_time - self._window_start)
                if wait_time > 0:
                    logger.warning(
                        "Rate limit reached. Waiting %.1f seconds...",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    self._request_count = 0
                    self._window_start = time.time()

            # Enforce minimum interval between requests
            elapsed = current_time - self._last_request_time
            if elapsed < self.MIN_REQUEST_INTERVAL:
                await asyncio.sleep(self.MIN_REQUEST_INTERVAL - elapsed)

            self._last_request_time = time.time()
            self._request_count += 1

    async def _call_gemini(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """
        Call Gemini API with retry logic.

        Args:
            prompt: The user prompt to send to Gemini
            system_prompt: The system prompt to use (default: SYSTEM_PROMPT)

        Returns:
            Raw response text from Gemini

        Raises:
            GeminiAPIError: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Apply rate limiting
                await self._rate_limit()

                logger.debug(
                    "Calling Gemini API (attempt %d/%d)",
                    attempt + 1,
                    self.MAX_RETRIES,
                )

                # Make the API call
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    [
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["I understand. I will extract ALL available financial data and return valid JSON."]},
                        {"role": "user", "parts": [prompt]},
                    ],
                )

                # Extract text from response
                if response.text:
                    logger.debug("Gemini API call successful")
                    return response.text
                else:
                    raise GeminiAPIError("Empty response from Gemini API")

            except Exception as e:
                last_error = e
                logger.warning(
                    "Gemini API call failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    str(e),
                )

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)  # Exponential backoff
                    logger.info("Retrying in %.1f seconds...", delay)
                    await asyncio.sleep(delay)

        raise GeminiAPIError(
            f"All {self.MAX_RETRIES} API call attempts failed: {last_error}"
        )

    def _parse_response(self, response: str) -> StandardizedValuationInput:
        """
        Parse and validate AI response into StandardizedValuationInput.

        Args:
            response: Raw response text from Gemini

        Returns:
            Validated StandardizedValuationInput instance

        Raises:
            InvalidResponseError: If response cannot be parsed or validated
        """
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned = response.strip()

            # Remove markdown code fences
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Find JSON object boundaries
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1

            if start_idx == -1 or end_idx <= start_idx:
                raise InvalidResponseError(
                    f"No valid JSON object found in response: {cleaned[:200]}..."
                )

            json_str = cleaned[start_idx:end_idx]

            # Parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                json_str = self._fix_json(json_str)
                data = json.loads(json_str)

            # Validate with Pydantic
            result = StandardizedValuationInput.model_validate(data)

            logger.info(
                "Successfully parsed extraction for %s (confidence: %.2f)",
                result.ticker,
                result.data_confidence_score,
            )

            return result

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise InvalidResponseError(f"Failed to validate response: {e}")

    def _fix_json(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string
        """
        # Replace single quotes with double quotes
        # (but not inside strings - simple heuristic)
        fixed = json_str

        # Remove trailing commas before } or ]
        fixed = re.sub(r",\s*([\}\]])", r"\1", fixed)

        # Fix unquoted keys (simple cases)
        fixed = re.sub(r"(\{|\,)\s*(\w+)\s*:", r'\1"\2":', fixed)

        return fixed

    def _prepare_prompt_data(self, stock_data: dict) -> dict:
        """
        Prepare data sections for prompt construction.

        Args:
            stock_data: Truncated stock data dict

        Returns:
            Dict with formatted JSON strings for each section
        """
        def safe_json(data: Any, default: str = "{}") -> str:
            """Safely convert data to JSON string."""
            if data is None:
                return default
            try:
                return json.dumps(data, indent=2, default=str)
            except Exception:
                return default

        yahoo = stock_data.get("yahoo_financials", {})

        return {
            "company_info_json": safe_json(stock_data.get("company_info")),
            "market_data_json": safe_json(stock_data.get("market_data")),
            "valuation_json": safe_json(stock_data.get("valuation")),
            "calculated_metrics_json": safe_json(stock_data.get("calculated_metrics")),
            "financials_annual_json": safe_json(stock_data.get("financials_annual")),
            "income_quarterly_json": safe_json(
                yahoo.get("income_statement_quarterly")
                or yahoo.get("income_statement_annual")
            ),
            "balance_sheet_json": safe_json(
                yahoo.get("balance_sheet_quarterly")
                or yahoo.get("balance_sheet_annual")
            ),
            "cashflow_quarterly_json": safe_json(
                yahoo.get("cash_flow_statement_quarterly")
                or yahoo.get("cash_flow_statement_annual")
            ),
        }

    async def extract_valuation_input(
        self,
        ticker: str,
        force_refresh: bool = False,
    ) -> StandardizedValuationInput:
        """
        Extract standardized valuation input for a stock.

        This is the main entry point for the extraction service. It handles
        caching, data loading, prompt construction, API calls, and validation.

        Args:
            ticker: Stock ticker symbol (case-insensitive)
            force_refresh: If True, bypass cache and force new extraction

        Returns:
            StandardizedValuationInput with extracted and normalized data

        Raises:
            DataNotFoundError: If stock JSON file is not found
            GeminiAPIError: If API call fails after retries
            InvalidResponseError: If AI response cannot be parsed
        """
        ticker = ticker.upper().strip()
        logger.info("Starting extraction for %s (force_refresh=%s)", ticker, force_refresh)

        # Load stock data first to get collected_at for cache key
        settings = get_settings()
        json_path = settings.json_dir_resolved / f"{ticker}.json"

        if not json_path.exists():
            raise DataNotFoundError(f"Stock data file not found: {json_path}")

        # Load full stock data
        stock_data = load_stock_json(ticker)
        collected_at = stock_data.get("collected_at", "")

        # Check cache (unless force refresh)
        if not force_refresh:
            cached = self.cache.get(ticker, collected_at)
            if cached is not None:
                logger.info("Returning cached extraction for %s", ticker)
                return cached

        # Truncate data for API efficiency
        truncated_data = self.truncate_json(stock_data)

        # Prepare prompt data
        prompt_data = self._prepare_prompt_data(truncated_data)

        # Get market data for prompt
        market_data = stock_data.get("market_data", {})
        current_price = market_data.get("current_price", 0)
        market_cap = market_data.get("market_cap", 0)
        company_name = stock_data.get("company_name", ticker)

        # Build user prompt
        user_prompt = build_user_prompt(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            market_cap=market_cap,
            collected_at=collected_at,
            **prompt_data,
        )

        # Call Gemini API
        logger.info("Calling Gemini API for %s extraction...", ticker)
        response = await self._call_gemini(user_prompt)

        # Parse and validate response
        result = self._parse_response(response)

        # Cache the result
        self.cache.set(ticker, result, collected_at)

        logger.info(
            "Extraction complete for %s (confidence: %.2f, missing: %d, estimated: %d)",
            ticker,
            result.data_confidence_score,
            len(result.missing_fields),
            len(result.estimated_fields),
        )

        return result

    def _parse_flexible_response(self, response: str) -> FlexibleValuationInput:
        """
        Parse AI response into FlexibleValuationInput.

        This parser is more lenient and accepts whatever the AI returns.
        """
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned = response.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Find JSON object boundaries
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1

            if start_idx == -1 or end_idx <= start_idx:
                raise InvalidResponseError(
                    f"No valid JSON object found in response: {cleaned[:200]}..."
                )

            json_str = cleaned[start_idx:end_idx]

            # Parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                json_str = self._fix_json(json_str)
                data = json.loads(json_str)

            # Validate with flexible Pydantic model
            result = FlexibleValuationInput.model_validate(data)

            logger.info(
                "Flexible extraction for %s: confidence=%.2f, found=%d fields, missing=%d fields",
                result.ticker,
                result.data_confidence_score,
                len(result.data_quality.fields_found),
                len(result.data_quality.fields_missing),
            )

            return result

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise InvalidResponseError(f"Failed to validate response: {e}")

    async def extract_flexible(
        self,
        ticker: str,
        force_refresh: bool = False,
    ) -> FlexibleValuationInput:
        """
        Extract financial data using flexible approach.

        This method lets the AI extract ALL available data without
        forcing a rigid schema. The AI decides what to extract.

        Args:
            ticker: Stock ticker symbol
            force_refresh: If True, bypass cache

        Returns:
            FlexibleValuationInput with whatever data AI could extract
        """
        ticker = ticker.upper().strip()
        logger.info("Starting FLEXIBLE extraction for %s", ticker)

        # Load stock data
        settings = get_settings()
        json_path = settings.json_dir_resolved / f"{ticker}.json"

        if not json_path.exists():
            raise DataNotFoundError(f"Stock data file not found: {json_path}")

        stock_data = load_stock_json(ticker)
        collected_at = stock_data.get("collected_at", "")

        # Truncate data for API efficiency
        truncated_data = self.truncate_json(stock_data)

        # Prepare prompt data with calculated_metrics as priority
        yahoo = truncated_data.get("yahoo_financials", {})

        def safe_json(data: Any, default: str = "{}") -> str:
            if data is None:
                return default
            try:
                return json.dumps(data, indent=2, default=str)
            except Exception:
                return default

        # Get market data
        market_data = stock_data.get("market_data", {})
        current_price = market_data.get("current_price", 0)
        market_cap = market_data.get("market_cap", 0)
        company_name = stock_data.get("company_name", ticker)

        # Build flexible prompt
        user_prompt = build_flexible_prompt(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            market_cap=market_cap,
            collected_at=collected_at,
            calculated_metrics_json=safe_json(stock_data.get("calculated_metrics")),
            valuation_json=safe_json(stock_data.get("valuation")),
            market_data_json=safe_json(market_data),
            company_info_json=safe_json(stock_data.get("company_info")),
            cashflow_quarterly_json=safe_json(
                yahoo.get("cash_flow_statement_quarterly")
                or yahoo.get("cash_flow_quarterly")
            ),
            income_quarterly_json=safe_json(
                yahoo.get("income_statement_quarterly")
            ),
            income_annual_json=safe_json(
                yahoo.get("income_statement_annual")
            ),
            balance_sheet_json=safe_json(
                yahoo.get("balance_sheet_quarterly")
            ),
            financials_annual_json=safe_json(truncated_data.get("financials_annual")),
        )

        # Call Gemini with flexible system prompt
        logger.info("Calling Gemini API for %s flexible extraction...", ticker)
        response = await self._call_gemini(user_prompt, FLEXIBLE_SYSTEM_PROMPT)

        # Parse with flexible model
        result = self._parse_flexible_response(response)

        logger.info(
            "Flexible extraction complete for %s (confidence: %.2f)",
            ticker,
            result.data_confidence_score,
        )

        return result


@lru_cache(maxsize=1)
def get_ai_extractor() -> AIExtractor:
    """
    Get or create the singleton AIExtractor instance.

    This function provides a FastAPI-compatible dependency.
    Uses lru_cache for thread-safe lazy initialization without blocking
    the async event loop.

    Returns:
        AIExtractor: The singleton extractor instance.

    Raises:
        APIKeyNotConfiguredError: If GOOGLE_API_KEY is not set.

    Example:
        @router.get("/{ticker}/extraction")
        async def get_extraction(
            ticker: str,
            extractor: AIExtractor = Depends(get_ai_extractor)
        ):
            return await extractor.extract_valuation_input(ticker)
    """
    try:
        return AIExtractor()
    except ValueError as e:
        # Re-raise as a specific exception for better handling
        raise APIKeyNotConfiguredError(str(e)) from e
