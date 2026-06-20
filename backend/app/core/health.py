"""Readiness checks for load balancers / orchestrators.

Liveness ("am I running") is the static /health endpoint. Readiness ("can I serve
traffic") verifies dependencies: data + API key always, and Postgres/Redis when
they are configured.
"""

from __future__ import annotations

from sqlalchemy import text

from app.config import get_settings
from app.core.redis_client import is_redis_enabled
from app.core.redis_client import ping as redis_ping
from app.db.session import get_sessionmaker, is_enabled


async def _check_db() -> bool:
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - network dependent
        return False


async def check_readiness() -> tuple[bool, dict[str, str]]:
    """Return (healthy, per-dependency status)."""
    settings = get_settings()
    checks: dict[str, str] = {}

    checks["google_api_key"] = "ok" if settings.GOOGLE_API_KEY else "missing"

    json_dir = settings.json_dir_resolved
    has_data = json_dir.exists() and any(json_dir.glob("*.json"))
    checks["data_dir"] = "ok" if has_data else "missing"

    if is_enabled():
        checks["database"] = "ok" if await _check_db() else "down"
    if is_redis_enabled():
        checks["redis"] = "ok" if await redis_ping() else "down"

    healthy = all(status == "ok" for status in checks.values())
    return healthy, checks
