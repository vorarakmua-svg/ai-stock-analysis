"""Tests for the pluggable cache backends and the domain caches on Redis."""

import fnmatch

import pytest

from app.core.cache_backend import (
    DiskCacheBackend,
    RedisCacheBackend,
    make_cache_backend,
)


class FakeRedis:
    """Minimal sync Redis stand-in (decode_responses semantics)."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def delete(self, *keys):
        n = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                n += 1
        return n

    def scan_iter(self, match=None):
        return [k for k in list(self.store) if match is None or fnmatch.fnmatch(k, match)]

    def close(self):
        pass


# ---------------------------------------------------------------------------
# DiskCacheBackend
# ---------------------------------------------------------------------------
def test_disk_backend_roundtrip(tmp_path):
    b = DiskCacheBackend(tmp_path / "c")
    assert b.get("k") is None
    b.set("k", {"a": 1}, ttl=60)
    assert b.get("k") == {"a": 1}
    assert "k" in b.iter_keys()
    assert b.delete("k") is True
    assert b.get("k") is None
    assert b.stats()["backend"] == "disk"


# ---------------------------------------------------------------------------
# RedisCacheBackend (fake client)
# ---------------------------------------------------------------------------
def test_redis_backend_roundtrip_and_namespacing():
    client = FakeRedis()
    b = RedisCacheBackend(client, namespace="extractions")

    assert b.get("AAPL_x") is None
    b.set("AAPL_x", {"ticker": "AAPL"}, ttl=60)
    assert b.get("AAPL_x") == {"ticker": "AAPL"}
    # Stored under the namespace prefix.
    assert "extractions:AAPL_x" in client.store
    # iter_keys returns the un-prefixed keys.
    assert b.iter_keys() == ["AAPL_x"]
    assert b.delete("AAPL_x") is True
    assert b.get("AAPL_x") is None


def test_redis_backend_clear_only_touches_namespace():
    client = FakeRedis()
    client.store["other:keep"] = "1"
    b = RedisCacheBackend(client, namespace="valuations")
    b.set("k1", {"v": 1}, ttl=60)
    b.set("k2", {"v": 2}, ttl=60)

    b.clear()

    assert b.iter_keys() == []
    assert "other:keep" in client.store  # untouched


# ---------------------------------------------------------------------------
# make_cache_backend selection
# ---------------------------------------------------------------------------
def test_make_backend_defaults_to_disk(monkeypatch, tmp_path):
    from app.config import get_settings

    monkeypatch.setenv("CACHE_BACKEND", "disk")
    get_settings.cache_clear()
    try:
        backend = make_cache_backend("extractions")
        assert isinstance(backend, DiskCacheBackend)
    finally:
        get_settings.cache_clear()


def test_make_backend_redis_requires_url(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.delenv("REDIS_URL", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError):
            make_cache_backend("extractions")
    finally:
        get_settings.cache_clear()


def test_make_backend_redis_selected(monkeypatch):
    import redis

    from app.config import get_settings

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(redis.Redis, "from_url", classmethod(lambda cls, *a, **k: FakeRedis()))
    get_settings.cache_clear()
    try:
        backend = make_cache_backend("valuations")
        assert isinstance(backend, RedisCacheBackend)
    finally:
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Domain cache on a Redis backend (end-to-end serialization)
# ---------------------------------------------------------------------------
def test_extraction_cache_roundtrip_on_redis_backend():
    from app.core.cache_manager import ExtractionCache
    from tests.fixtures.sample_inputs import make_input

    cache = ExtractionCache(backend=RedisCacheBackend(FakeRedis(), "extractions"))
    inp = make_input(ticker="AAPL")

    assert cache.get("AAPL", "2024-01-01") is None
    cache.set("AAPL", inp, "2024-01-01")
    restored = cache.get("AAPL", "2024-01-01")

    assert restored is not None
    assert restored.ticker == "AAPL"
