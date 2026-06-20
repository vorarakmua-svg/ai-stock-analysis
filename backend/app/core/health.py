"""Readiness checks for load balancers / orchestrators.

Liveness ("am I running") is the static /health endpoint. Readiness ("can I serve
traffic") verifies dependencies. Postgres/Redis checks are added in P6.
"""

from __future__ import annotations

from app.config import get_settings


def check_readiness() -> tuple[bool, dict[str, str]]:
    """Return (healthy, per-dependency status)."""
    settings = get_settings()
    checks: dict[str, str] = {}

    checks["google_api_key"] = "ok" if settings.GOOGLE_API_KEY else "missing"

    json_dir = settings.json_dir_resolved
    has_data = json_dir.exists() and any(json_dir.glob("*.json"))
    checks["data_dir"] = "ok" if has_data else "missing"

    healthy = all(status == "ok" for status in checks.values())
    return healthy, checks
