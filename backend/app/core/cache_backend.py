"""Pluggable cache storage backend (diskcache or Redis).

The domain caches (ExtractionCache / ValuationCache / AnalysisCache) keep their
sync interface and Pydantic (de)serialization; only the underlying key/value
store is swapped here, selected by ``settings.CACHE_BACKEND``:

- ``disk`` (default): per-node ``diskcache`` — unchanged local behavior.
- ``redis``: a shared store so multiple app instances share one cache (unblocks
  horizontal scaling and avoids N× LLM spend across replicas). Requires REDIS_URL.

A sync Redis client is used deliberately: the existing caches are called
synchronously from the (already-async) services, exactly as diskcache was, so no
call sites change.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.config import get_settings

logger = logging.getLogger(__name__)


@runtime_checkable
class CacheBackend(Protocol):
    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict, ttl: int) -> None: ...
    def delete(self, key: str) -> bool: ...
    def iter_keys(self) -> list[str]: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...
    def stats(self) -> dict: ...


class DiskCacheBackend:
    """diskcache-backed store (the original local behavior)."""

    def __init__(self, cache_dir: Path) -> None:
        from diskcache import Cache

        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(cache_dir))

    def get(self, key: str) -> dict | None:
        value = self._cache.get(key)
        return value if isinstance(value, dict) else None

    def set(self, key: str, value: dict, ttl: int) -> None:
        self._cache.set(key, value, expire=ttl)

    def delete(self, key: str) -> bool:
        return bool(self._cache.delete(key))

    def iter_keys(self) -> list[str]:
        return [k for k in self._cache if isinstance(k, str)]

    def clear(self) -> None:
        self._cache.clear()

    def close(self) -> None:
        self._cache.close()

    def stats(self) -> dict:
        return {
            "backend": "disk",
            "size": len(self._cache),
            "volume": self._cache.volume(),
            "directory": str(self._cache.directory),
        }


class RedisCacheBackend:
    """Redis-backed store (shared across instances). Keys are namespaced."""

    def __init__(self, client: Any, namespace: str) -> None:
        self._client = client
        self._ns = namespace

    def _k(self, key: str) -> str:
        return f"{self._ns}:{key}"

    def get(self, key: str) -> dict | None:
        raw = self._client.get(self._k(key))
        if raw is None:
            return None
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def set(self, key: str, value: dict, ttl: int) -> None:
        self._client.set(self._k(key), json.dumps(value), ex=ttl)

    def delete(self, key: str) -> bool:
        return bool(self._client.delete(self._k(key)))

    def iter_keys(self) -> list[str]:
        prefix = f"{self._ns}:"
        return [k[len(prefix) :] for k in self._client.scan_iter(match=f"{prefix}*")]

    def clear(self) -> None:
        keys = list(self._client.scan_iter(match=f"{self._ns}:*"))
        if keys:
            self._client.delete(*keys)

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:  # pragma: no cover - best-effort
            pass

    def stats(self) -> dict:
        return {"backend": "redis", "namespace": self._ns}


def make_cache_backend(namespace: str) -> CacheBackend:
    """Build the configured backend for a given namespace (e.g. 'extractions')."""
    settings = get_settings()
    if settings.CACHE_BACKEND.lower() == "redis":
        if not settings.REDIS_URL:
            raise RuntimeError("CACHE_BACKEND=redis requires REDIS_URL to be set")
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Cache backend: redis (namespace=%s)", namespace)
        return RedisCacheBackend(client, namespace)

    cache_dir = settings.cache_dir_resolved / namespace
    logger.info("Cache backend: disk (%s)", cache_dir)
    return DiskCacheBackend(cache_dir)
