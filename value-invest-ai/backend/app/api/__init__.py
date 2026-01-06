"""
API module.

Contains all API versions and common dependencies.
"""

from app.api.deps import get_db_session, DbSession

__all__ = [
    "get_db_session",
    "DbSession",
]
