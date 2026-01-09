"""
File-based cache management for AI extraction results.

This module provides a persistent caching layer using diskcache to store
AI-extracted valuation inputs. Caching reduces API costs and improves
response times for frequently accessed stocks.

Cache Strategy:
- Key: {ticker}_{collected_at_hash} - ensures cache invalidation on data refresh
- TTL: 7 days (configurable via EXTRACTION_CACHE_TTL)
- Storage: Local disk using diskcache.Cache
"""

import hashlib
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional

from diskcache import Cache

from app.config import get_settings
from app.models.valuation_input import StandardizedValuationInput

logger = logging.getLogger(__name__)


class ExtractionCache:
    """
    Persistent cache for AI-extracted valuation data.

    Uses diskcache for local file-based caching with automatic TTL expiration.
    Cache keys incorporate both ticker and data collection timestamp to ensure
    cache invalidation when source data is refreshed.

    Attributes:
        cache: diskcache.Cache instance
        ttl: Cache TTL in seconds (default: 7 days)

    Example:
        cache = ExtractionCache()
        data = cache.get("AAPL")
        if data is None:
            data = extractor.extract(...)
            cache.set("AAPL", data)
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the extraction cache.

        Args:
            cache_dir: Optional custom cache directory. If not provided,
                      uses settings.cache_dir_resolved / "extractions"
        """
        settings = get_settings()
        self.ttl = settings.EXTRACTION_CACHE_TTL

        if cache_dir is None:
            cache_dir = settings.cache_dir_resolved / "extractions"

        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache = Cache(str(cache_dir))
        logger.info(
            "ExtractionCache initialized at %s with TTL=%d seconds",
            cache_dir,
            self.ttl,
        )

    def get_cache_key(self, ticker: str, collected_at: Optional[str] = None) -> str:
        """
        Generate a cache key for a ticker.

        The key incorporates the ticker and optionally a hash of the collection
        timestamp to ensure cache invalidation when source data changes.

        Args:
            ticker: Stock ticker symbol (case-insensitive)
            collected_at: ISO 8601 timestamp of data collection. If provided,
                         a hash is appended to the key for cache busting.

        Returns:
            Cache key string in format "TICKER" or "TICKER_hash"

        Example:
            >>> cache.get_cache_key("AAPL", "2026-01-07T10:30:00")
            "AAPL_a1b2c3d4"
        """
        ticker = ticker.upper().strip()

        if collected_at:
            # Create a short hash of the collection timestamp
            hash_str = hashlib.md5(collected_at.encode()).hexdigest()[:8]
            return f"{ticker}_{hash_str}"

        return ticker

    def get(
        self,
        ticker: str,
        collected_at: Optional[str] = None,
    ) -> Optional[StandardizedValuationInput]:
        """
        Retrieve cached extraction data for a ticker.

        Args:
            ticker: Stock ticker symbol
            collected_at: Optional collection timestamp for cache key generation

        Returns:
            StandardizedValuationInput if found and valid, None otherwise.

        Note:
            Returns None if the cached data is expired or invalid.
        """
        cache_key = self.get_cache_key(ticker, collected_at)

        try:
            cached_data = self.cache.get(cache_key)

            if cached_data is None:
                logger.debug("Cache miss for %s (key: %s)", ticker, cache_key)
                return None

            # Validate and deserialize the cached data
            if isinstance(cached_data, dict):
                result = StandardizedValuationInput.model_validate(cached_data)
                logger.debug(
                    "Cache hit for %s (key: %s, timestamp: %s)",
                    ticker,
                    cache_key,
                    result.extraction_timestamp,
                )
                return result

            logger.warning(
                "Invalid cached data type for %s: %s",
                ticker,
                type(cached_data),
            )
            return None

        except Exception as e:
            logger.warning(
                "Failed to retrieve cache for %s: %s",
                ticker,
                str(e),
            )
            return None

    def set(
        self,
        ticker: str,
        data: StandardizedValuationInput,
        collected_at: Optional[str] = None,
    ) -> None:
        """
        Store extraction data in the cache.

        Args:
            ticker: Stock ticker symbol
            data: StandardizedValuationInput to cache
            collected_at: Optional collection timestamp for cache key generation

        Note:
            Data is serialized to dict for storage.
            TTL is automatically applied from settings.
        """
        cache_key = self.get_cache_key(ticker, collected_at)

        try:
            # Serialize to dict for storage
            cache_data = data.model_dump(mode="json")
            self.cache.set(cache_key, cache_data, expire=self.ttl)

            logger.info(
                "Cached extraction for %s (key: %s, TTL: %d seconds)",
                ticker,
                cache_key,
                self.ttl,
            )

        except Exception as e:
            logger.error(
                "Failed to cache extraction for %s: %s",
                ticker,
                str(e),
            )

    def invalidate(self, ticker: str, collected_at: Optional[str] = None) -> bool:
        """
        Invalidate (delete) cached data for a ticker.

        Args:
            ticker: Stock ticker symbol
            collected_at: Optional collection timestamp for specific key

        Returns:
            True if deletion was successful, False otherwise.
        """
        cache_key = self.get_cache_key(ticker, collected_at)

        try:
            deleted = self.cache.delete(cache_key)

            if deleted:
                logger.info("Invalidated cache for %s (key: %s)", ticker, cache_key)
            else:
                logger.debug(
                    "No cache entry found to invalidate for %s (key: %s)",
                    ticker,
                    cache_key,
                )

            return deleted

        except Exception as e:
            logger.error(
                "Failed to invalidate cache for %s: %s",
                ticker,
                str(e),
            )
            return False

    def invalidate_all(self, ticker: str) -> int:
        """
        Invalidate all cached entries for a ticker (all collection timestamps).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Number of entries deleted.
        """
        ticker = ticker.upper().strip()
        deleted_count = 0

        try:
            # Iterate through all keys and delete those matching the ticker
            for key in list(self.cache):
                if isinstance(key, str) and key.startswith(f"{ticker}_"):
                    if self.cache.delete(key):
                        deleted_count += 1

            # Also delete the base key without timestamp
            if self.cache.delete(ticker):
                deleted_count += 1

            logger.info(
                "Invalidated %d cache entries for %s",
                deleted_count,
                ticker,
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "Failed to invalidate all caches for %s: %s",
                ticker,
                str(e),
            )
            return deleted_count

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics including size and volume.
        """
        try:
            return {
                "size": len(self.cache),
                "volume": self.cache.volume(),
                "directory": str(self.cache.directory),
            }
        except Exception as e:
            logger.error("Failed to get cache stats: %s", str(e))
            return {"error": str(e)}

    def clear(self) -> None:
        """Clear all entries from the cache."""
        try:
            self.cache.clear()
            logger.info("Cleared all extraction cache entries")
        except Exception as e:
            logger.error("Failed to clear cache: %s", str(e))

    def close(self) -> None:
        """Close the cache connection."""
        try:
            self.cache.close()
            logger.debug("Extraction cache closed")
        except Exception as e:
            logger.error("Failed to close cache: %s", str(e))

    def __enter__(self) -> "ExtractionCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close the cache."""
        self.close()


@lru_cache(maxsize=1)
def get_extraction_cache() -> ExtractionCache:
    """
    Get or create the singleton ExtractionCache instance.

    This function provides a FastAPI-compatible dependency for cache access.
    Uses lru_cache for thread-safe lazy initialization without blocking
    the async event loop.

    Returns:
        ExtractionCache: The singleton cache instance.

    Example:
        @router.get("/{ticker}/extraction")
        async def get_extraction(
            ticker: str,
            cache: ExtractionCache = Depends(get_extraction_cache)
        ):
            return cache.get(ticker)
    """
    return ExtractionCache()
