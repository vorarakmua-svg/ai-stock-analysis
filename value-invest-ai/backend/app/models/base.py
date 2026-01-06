"""
Base model class for SQLAlchemy models.

This module provides the declarative base and common mixins for all models.
Uses SQLAlchemy 2.0 style with async support.

The Base class is re-exported from database.py for convenience.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

# Re-export Base from database module for consistent import patterns
from app.database import Base


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    These columns are automatically managed:
    - created_at: Set to current UTC time on insert
    - updated_at: Set to current UTC time on insert and update
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class TableNameMixin:
    """
    Mixin that provides automatic table name generation.

    Converts CamelCase class names to snake_case table names.
    Example: IncomeStatement -> income_statements
    """

    @classmethod
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        import re
        # Convert CamelCase to snake_case and pluralize
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Simple pluralization (add 's' or 'es')
        if name.endswith('s') or name.endswith('x') or name.endswith('z'):
            return f"{name}es"
        elif name.endswith('y'):
            return f"{name[:-1]}ies"
        return f"{name}s"


# Export commonly used types for model definitions
__all__ = [
    "Base",
    "TimestampMixin",
    "TableNameMixin",
]
