"""
AI Investment Analyst service using Google Gemini.

This module provides the AIAnalyst class that generates Warren Buffett-style
investment analysis memos based on valuation results and company data.

Architecture Notes:
- AI Layer handles: Qualitative analysis, narrative generation, investment recommendations
- AI Layer receives: Pre-computed valuation results from Python valuation engine
- AI Layer does NOT: Perform mathematical calculations, make up financial numbers

Rate Limiting:
- Gemini API: Max 15 requests/minute (conservative limit for analysis generation)
- Implemented with time-based throttling and request counting

Caching:
- Analysis results cached for 7 days (ANALYSIS_CACHE_TTL)
- Cache key includes ticker and valuation timestamp for invalidation
"""

import asyncio
import hashlib
import json
import logging
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import google.generativeai as genai
from diskcache import Cache

from app.config import get_settings
from app.core.data_loader import load_stock_json
from app.models.analysis import WarrenBuffettAnalysis
from app.models.valuation_output import ValuationResult
from app.prompts.analysis_prompt import (
    BUFFETT_SYSTEM_PROMPT,
    build_analysis_prompt,
)
from app.services.valuation_engine import (
    FlexibleInputAdapter,
    ValuationEngine,
    get_valuation_engine,
)

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Base exception for analysis errors."""

    pass


class GeminiAnalysisError(AnalysisError):
    """Exception raised when Gemini API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class InvalidAnalysisError(AnalysisError):
    """Exception raised when AI response cannot be parsed."""

    pass


class ValuationNotFoundError(AnalysisError):
    """Exception raised when valuation data is not available."""

    pass


class AnalysisCache:
    """
    Persistent cache for AI-generated analysis results.

    Uses diskcache for local file-based caching with 7-day TTL.
    Cache keys incorporate ticker and valuation timestamp to ensure
    cache invalidation when underlying valuation changes.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the analysis cache.

        Args:
            cache_dir: Optional custom cache directory. If not provided,
                      uses settings.cache_dir_resolved / "analyses"
        """
        settings = get_settings()
        self.ttl = settings.ANALYSIS_CACHE_TTL

        if cache_dir is None:
            cache_dir = settings.cache_dir_resolved / "analyses"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(cache_dir))

        logger.info(
            "AnalysisCache initialized at %s with TTL=%d seconds (%.1f days)",
            cache_dir,
            self.ttl,
            self.ttl / 86400,
        )

    def _get_cache_key(self, ticker: str, valuation_timestamp: str) -> str:
        """Generate cache key from ticker and valuation timestamp."""
        ticker = ticker.upper().strip()
        hash_str = hashlib.md5(valuation_timestamp.encode()).hexdigest()[:8]
        return f"analysis_{ticker}_{hash_str}"

    def get(
        self,
        ticker: str,
        valuation_timestamp: str,
    ) -> Optional[WarrenBuffettAnalysis]:
        """
        Retrieve cached analysis for a ticker.

        Args:
            ticker: Stock ticker symbol
            valuation_timestamp: ISO timestamp from valuation

        Returns:
            WarrenBuffettAnalysis if found and valid, None otherwise.
        """
        cache_key = self._get_cache_key(ticker, valuation_timestamp)

        try:
            cached_data = self.cache.get(cache_key)

            if cached_data is None:
                logger.debug("Analysis cache miss for %s", ticker)
                return None

            if isinstance(cached_data, dict):
                result = WarrenBuffettAnalysis.model_validate(cached_data)
                logger.debug(
                    "Analysis cache hit for %s (date: %s)",
                    ticker,
                    result.analysis_date,
                )
                return result

            return None

        except Exception as e:
            logger.warning("Failed to retrieve cached analysis for %s: %s", ticker, e)
            return None

    def set(
        self,
        ticker: str,
        data: WarrenBuffettAnalysis,
        valuation_timestamp: str,
    ) -> None:
        """
        Store analysis result in cache.

        Args:
            ticker: Stock ticker symbol
            data: WarrenBuffettAnalysis to cache
            valuation_timestamp: ISO timestamp from valuation
        """
        cache_key = self._get_cache_key(ticker, valuation_timestamp)

        try:
            cache_data = data.model_dump(mode="json")
            self.cache.set(cache_key, cache_data, expire=self.ttl)
            logger.info(
                "Cached analysis for %s (TTL: %d seconds)",
                ticker,
                self.ttl,
            )
        except Exception as e:
            logger.error("Failed to cache analysis for %s: %s", ticker, e)

    def invalidate(self, ticker: str) -> int:
        """Invalidate all cached analyses for a ticker."""
        ticker = ticker.upper().strip()
        deleted_count = 0

        try:
            for key in list(self.cache):
                if isinstance(key, str) and key.startswith(f"analysis_{ticker}_"):
                    if self.cache.delete(key):
                        deleted_count += 1

            logger.info("Invalidated %d analysis cache entries for %s", deleted_count, ticker)
            return deleted_count

        except Exception as e:
            logger.error("Failed to invalidate analyses for %s: %s", ticker, e)
            return deleted_count


class AIAnalyst:
    """
    AI-powered investment analyst using Google Gemini Pro.

    This class generates Warren Buffett-style investment analysis memos
    based on valuation results and company financial data.

    Attributes:
        model: Gemini GenerativeModel instance
        cache: AnalysisCache for result caching
        valuation_engine: ValuationEngine for getting valuation results

    Example:
        analyst = AIAnalyst()
        analysis = await analyst.generate_analysis("AAPL")
    """

    # Rate limiting constants (conservative for analysis generation)
    MAX_REQUESTS_PER_MINUTE = 15
    MIN_REQUEST_INTERVAL = 4.0  # Minimum seconds between requests

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 3.0  # Base delay in seconds

    def __init__(
        self,
        cache: Optional[AnalysisCache] = None,
        valuation_engine: Optional[ValuationEngine] = None,
    ) -> None:
        """
        Initialize the AI analyst.

        Args:
            cache: Optional AnalysisCache instance. If not provided,
                  creates a new default cache.
            valuation_engine: Optional ValuationEngine. If not provided,
                            uses the singleton instance.

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

        # Initialize model with appropriate settings for Buffett-style analysis
        # Model options for investment reasoning (choose based on needs):
        # - "gemini-2.5-pro": Best reasoning, deep analysis (RECOMMENDED for Buffett)
        # - "gemini-2.5-flash": Good reasoning, faster and cheaper
        # - "gemini-2.0-flash-thinking-exp": Explicit chain-of-thought reasoning
        # - "gemini-2.0-flash": Fast but shallow reasoning (not ideal)
        # Configure via GEMINI_MODEL_NAME environment variable
        model_name = settings.GEMINI_MODEL_NAME
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=0.7,  # Higher temp for natural Buffett-style writing
                top_p=0.95,
                top_k=40,
                max_output_tokens=16384,  # Larger output for comprehensive analysis
            ),
        )

        # Initialize cache
        self.cache = cache or AnalysisCache()

        # Valuation engine (lazy loaded)
        self._valuation_engine = valuation_engine

        # Rate limiting state
        self._last_request_time: float = 0.0
        self._request_count: int = 0
        self._window_start: float = time.time()

        logger.info("AIAnalyst initialized with Gemini model: %s", model_name)

    @property
    def valuation_engine(self) -> ValuationEngine:
        """Lazy-load valuation engine to avoid circular imports."""
        if self._valuation_engine is None:
            self._valuation_engine = get_valuation_engine()
        return self._valuation_engine

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting for API calls.

        Ensures compliance with conservative Gemini API limits for analysis
        (15 requests/minute). Uses sliding window with minimum interval.
        """
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
                    "Analysis rate limit reached. Waiting %.1f seconds...",
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

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with retry logic.

        Args:
            prompt: The user prompt to send to Gemini

        Returns:
            Raw response text from Gemini

        Raises:
            GeminiAnalysisError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Apply rate limiting
                await self._rate_limit()

                logger.debug(
                    "Calling Gemini API for analysis (attempt %d/%d)",
                    attempt + 1,
                    self.MAX_RETRIES,
                )

                start_time = time.time()

                # Make the API call
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    [
                        {"role": "user", "parts": [BUFFETT_SYSTEM_PROMPT]},
                        {"role": "model", "parts": ["I understand. I am Warren Buffett, ready to analyze this investment opportunity using my time-tested value investing principles. I will return my analysis as a valid JSON object matching the WarrenBuffettAnalysis schema, with no markdown formatting."]},
                        {"role": "user", "parts": [prompt]},
                    ],
                )

                elapsed = time.time() - start_time

                # Extract text from response
                if response.text:
                    logger.debug(
                        "Gemini analysis call successful (%.2f seconds)",
                        elapsed,
                    )
                    return response.text
                else:
                    raise GeminiAnalysisError("Empty response from Gemini API")

            except Exception as e:
                last_error = e
                logger.warning(
                    "Gemini analysis call failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    str(e),
                )

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.info("Retrying analysis in %.1f seconds...", delay)
                    await asyncio.sleep(delay)

        raise GeminiAnalysisError(
            f"All {self.MAX_RETRIES} analysis API calls failed: {last_error}"
        )

    def _parse_response(
        self,
        response: str,
        generation_time: float,
    ) -> WarrenBuffettAnalysis:
        """
        Parse and validate AI response into WarrenBuffettAnalysis.

        Args:
            response: Raw response text from Gemini
            generation_time: Time taken to generate the response

        Returns:
            Validated WarrenBuffettAnalysis instance

        Raises:
            InvalidAnalysisError: If response cannot be parsed or validated
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
                raise InvalidAnalysisError(
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

            # Add generation metadata if not present
            if "generation_time_seconds" not in data or data.get("generation_time_seconds") is None:
                data["generation_time_seconds"] = generation_time

            # Validate with Pydantic
            result = WarrenBuffettAnalysis.model_validate(data)

            logger.info(
                "Successfully parsed analysis for %s (rating: %s, conviction: %.2f)",
                result.ticker,
                result.investment_rating.value,
                result.conviction_level,
            )

            return result

        except json.JSONDecodeError as e:
            raise InvalidAnalysisError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise InvalidAnalysisError(f"Failed to validate analysis response: {e}")

    def _fix_json(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string
        """
        fixed = json_str

        # Remove trailing commas before } or ]
        fixed = re.sub(r",\s*([\}\]])", r"\1", fixed)

        # Fix unquoted keys (simple cases)
        fixed = re.sub(r"(\{|\,)\s*(\w+)\s*:", r'\1"\2":', fixed)

        # Replace single quotes with double quotes in obvious cases
        # This is a risky operation, so we only do it as a last resort
        if "'" in fixed and '"' not in fixed:
            fixed = fixed.replace("'", '"')

        return fixed

    def _get_business_description(self, ticker: str) -> str:
        """
        Get business description from stock JSON data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Business description string or empty string if not found
        """
        try:
            stock_data = load_stock_json(ticker)
            company_info = stock_data.get("company_info", {})
            return company_info.get("business_summary", "") or company_info.get(
                "longBusinessSummary", ""
            )
        except Exception as e:
            logger.warning("Failed to load business description for %s: %s", ticker, e)
            return ""

    async def generate_analysis(
        self,
        ticker: str,
        force_refresh: bool = False,
    ) -> WarrenBuffettAnalysis:
        """
        Generate Warren Buffett-style investment analysis.

        This is the main entry point for analysis generation. It:
        1. Gets valuation result from valuation engine
        2. Checks cache for existing analysis (unless force_refresh)
        3. Builds analysis prompt with valuation data
        4. Calls Gemini API to generate analysis
        5. Parses and validates the response
        6. Caches and returns result

        Args:
            ticker: Stock ticker symbol
            force_refresh: If True, bypass cache and regenerate

        Returns:
            WarrenBuffettAnalysis with complete investment memo

        Raises:
            ValuationNotFoundError: If valuation cannot be obtained
            GeminiAnalysisError: If API call fails
            InvalidAnalysisError: If response cannot be parsed
        """
        ticker = ticker.upper().strip()
        logger.info(
            "Starting analysis for %s (force_refresh=%s)",
            ticker,
            force_refresh,
        )

        # Get valuation result first
        try:
            valuation_result = await self.valuation_engine.calculate_valuation(
                ticker,
                force_refresh=force_refresh,
            )
        except Exception as e:
            logger.error("Failed to get valuation for %s: %s", ticker, e)
            raise ValuationNotFoundError(
                f"Could not obtain valuation for {ticker}: {e}"
            ) from e

        valuation_timestamp = valuation_result.calculation_timestamp.isoformat()

        # Check cache (unless force refresh)
        if not force_refresh:
            cached = self.cache.get(ticker, valuation_timestamp)
            if cached is not None:
                logger.info("Returning cached analysis for %s", ticker)
                return cached

        # Get extraction data for additional context using flexible extraction
        try:
            flexible_data = await self.valuation_engine.ai_extractor.extract_flexible(
                ticker,
                force_refresh=False,  # Use cached extraction if available
            )
            # Wrap with adapter for flat property access
            extraction_data = FlexibleInputAdapter(flexible_data)
        except Exception as e:
            logger.error("Failed to get extraction data for %s: %s", ticker, e)
            raise ValuationNotFoundError(
                f"Could not obtain extraction data for {ticker}: {e}"
            ) from e

        # Get business description
        business_description = self._get_business_description(ticker)

        # Build analysis prompt
        user_prompt = build_analysis_prompt(
            valuation_result=valuation_result,
            extraction_data=extraction_data,
            business_description=business_description,
        )

        # Call Gemini API
        logger.info("Calling Gemini API for %s analysis...", ticker)
        start_time = time.time()

        response = await self._call_gemini(user_prompt)

        generation_time = time.time() - start_time

        # Parse and validate response
        result = self._parse_response(response, generation_time)

        # Cache the result
        self.cache.set(ticker, result, valuation_timestamp)

        logger.info(
            "Analysis complete for %s: rating=%s, conviction=%.2f, time=%.2fs",
            ticker,
            result.investment_rating.value,
            result.conviction_level,
            generation_time,
        )

        return result

    async def get_cached_analysis(
        self,
        ticker: str,
    ) -> Optional[WarrenBuffettAnalysis]:
        """
        Get cached analysis if available, without generating new one.

        This method is useful for checking if an analysis exists
        without triggering the expensive generation process.

        Args:
            ticker: Stock ticker symbol

        Returns:
            WarrenBuffettAnalysis if cached, None otherwise
        """
        ticker = ticker.upper().strip()

        # We need the valuation timestamp to find the cache entry
        # Try to get cached valuation first
        try:
            valuation_result = await self.valuation_engine.calculate_valuation(
                ticker,
                force_refresh=False,
            )
            valuation_timestamp = valuation_result.calculation_timestamp.isoformat()
            return self.cache.get(ticker, valuation_timestamp)
        except Exception:
            # If we can't get valuation, we can't find the cache entry
            return None


# Singleton instance for dependency injection
_analyst_instance: Optional[AIAnalyst] = None
_analyst_lock = threading.Lock()


def get_ai_analyst() -> AIAnalyst:
    """
    Get or create the singleton AIAnalyst instance.

    This function provides a FastAPI-compatible dependency.

    Returns:
        AIAnalyst: The singleton analyst instance.

    Raises:
        HTTPException: 503 if GOOGLE_API_KEY is not configured.

    Example:
        @router.get("/{ticker}/analysis")
        async def get_analysis(
            ticker: str,
            analyst: AIAnalyst = Depends(get_ai_analyst)
        ):
            return await analyst.generate_analysis(ticker)
    """
    from fastapi import HTTPException, status

    global _analyst_instance
    if _analyst_instance is None:
        with _analyst_lock:
            # Double-check after acquiring lock
            if _analyst_instance is None:
                try:
                    _analyst_instance = AIAnalyst()
                except ValueError as e:
                    # API key not configured - return proper HTTP error
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=str(e),
                    )
    return _analyst_instance
