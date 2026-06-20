"""Async engine / sessionmaker, created lazily from DATABASE_URL.

Persistence is optional: when DATABASE_URL is empty, ``is_enabled()`` is False
and callers skip all DB work, so the app runs unchanged without a database.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.config import get_settings


def is_enabled() -> bool:
    """True when a database is configured."""
    return bool(get_settings().DATABASE_URL)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Lazily create the async engine. Call only when is_enabled()."""
    url = get_settings().DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_async_engine(url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker:
    """Lazily create the async sessionmaker bound to the engine."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)
