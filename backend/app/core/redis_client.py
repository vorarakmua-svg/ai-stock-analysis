"""Async Redis client + a small JSON cache helper.

Optional: when REDIS_URL is empty, ``is_redis_enabled()`` is False and callers
fall back to the existing disk cache. Provided now as the substrate for moving
the multi-tier cache off per-node diskcache (unblocks horizontal scaling).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def is_redis_enabled() -> bool:
    return bool(get_settings().REDIS_URL)


@lru_cache(maxsize=1)
def get_redis():
    """Lazily create an async Redis client from REDIS_URL."""
    import redis.asyncio as redis

    url = get_settings().REDIS_URL
    if not url:
        raise RuntimeError("REDIS_URL is not configured")
    return redis.from_url(url, encoding="utf-8", decode_responses=True)


class RedisJSONCache:
    """Minimal async JSON cache with TTL, sharing the ExtractionCache key style.

    Takes an injected client so it is unit-testable against a fake.
    """

    def __init__(self, client: Any, namespace: str = "cache") -> None:
        self._client = client
        self._ns = namespace

    def _key(self, key: str) -> str:
        return f"{self._ns}:{key}"

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self._client.set(self._key(key), json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(self._key(key))


async def ping() -> bool:
    """Return True if Redis responds to PING (for readiness)."""
    try:
        return bool(await get_redis().ping())
    except Exception:  # pragma: no cover - network dependent
        return False
