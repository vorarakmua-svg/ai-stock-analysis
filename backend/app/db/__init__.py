"""Async persistence layer (SQLAlchemy 2.x).

Optional: when DATABASE_URL is empty the app runs file/disk-only and all
persistence calls are no-ops. This is the substrate for valuation history and
LLM usage metering, with a nullable owner_id placeholder so multi-tenancy can be
added later without a breaking migration.
"""

from app.db import models  # noqa: F401 - register ORM tables on Base.metadata
from app.db.base import Base
from app.db.session import get_sessionmaker, is_enabled

__all__ = ["Base", "get_sessionmaker", "is_enabled"]
