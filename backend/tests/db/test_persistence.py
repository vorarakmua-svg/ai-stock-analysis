"""Persistence layer tests against SQLite (aiosqlite) + a fake Redis client.

No Postgres/Redis server required; the same async SQLAlchemy code runs here that
runs against Postgres in production.
"""

import pytest
from sqlalchemy import select


@pytest.fixture
async def db(tmp_path, monkeypatch):
    """Enable persistence against a temp SQLite file and create the schema."""
    from app.config import get_settings
    from app.db import session as dbsession
    from app.db.base import Base

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    get_settings.cache_clear()
    dbsession.get_engine.cache_clear()
    dbsession.get_sessionmaker.cache_clear()

    engine = dbsession.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield dbsession

    await engine.dispose()
    get_settings.cache_clear()
    dbsession.get_engine.cache_clear()
    dbsession.get_sessionmaker.cache_clear()


async def test_is_enabled_reflects_setting(db):
    assert db.is_enabled() is True


async def test_save_and_query_valuation(db):
    from app.db import models
    from app.db.repository import save_valuation

    await save_valuation(
        ticker="AAPL",
        composite_intrinsic_value=150.0,
        verdict="UNDERVALUED",
        extraction_timestamp="2024-01-01T00:00:00+00:00",
        payload={"composite": 150.0},
    )

    async with db.get_sessionmaker()() as session:
        rows = (await session.execute(select(models.Valuation))).scalars().all()

    assert len(rows) == 1
    assert rows[0].ticker == "AAPL"
    assert rows[0].verdict == "UNDERVALUED"
    assert rows[0].payload == {"composite": 150.0}
    assert rows[0].owner_id is None  # multi-tenancy placeholder


async def test_save_llm_usage(db):
    from app.db import models
    from app.db.repository import save_llm_usage

    await save_llm_usage(
        purpose="extraction",
        model="gemini-2.5-flash",
        input_tokens=100,
        output_tokens=50,
        thinking_tokens=0,
        total_tokens=150,
        ticker="MSFT",
    )

    async with db.get_sessionmaker()() as session:
        rows = (await session.execute(select(models.LlmUsage))).scalars().all()

    assert len(rows) == 1
    assert rows[0].purpose == "extraction"
    assert rows[0].total_tokens == 150


async def test_repository_is_noop_when_db_disabled(monkeypatch):
    """With no DATABASE_URL, save_* are silent no-ops (no error, no connection)."""
    from app.config import get_settings
    from app.db.repository import save_valuation

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        await save_valuation(
            ticker="X",
            composite_intrinsic_value=1.0,
            verdict="v",
            extraction_timestamp="t",
            payload={},
        )  # must not raise
    finally:
        get_settings.cache_clear()


# --- Redis JSON cache (fake client) ----------------------------------------
class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, key):
        self.store.pop(key, None)


async def test_redis_json_cache_roundtrip():
    from app.core.redis_client import RedisJSONCache

    cache = RedisJSONCache(FakeRedis(), namespace="ns")
    assert await cache.get("missing") is None

    await cache.set("k", {"a": 1}, ttl=60)
    assert await cache.get("k") == {"a": 1}

    await cache.delete("k")
    assert await cache.get("k") is None
