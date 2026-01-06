"""
Database configuration and session management.

This module provides:
- Async SQLAlchemy engine and session factory
- Database session dependency for FastAPI
- Database initialization and health check functions
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    All models should inherit from this class to be included
    in migrations and table creation.
    """
    pass


# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL statements in debug mode
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically committed on success and rolled back on error.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in SQLAlchemy models.
    Safe to call multiple times - only creates tables that don't exist.
    """
    # Import all models to ensure they're registered with Base
    from app.models import (
        Company,
        IncomeStatement,
        BalanceSheet,
        CashFlowStatement,
        StockPrice,
        Valuation,
        AIAnalysis,
        DataFetchLog,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def get_db_info() -> dict:
    """
    Get database connection information.

    Returns:
        Dictionary with database version and connection details
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            return {
                "connected": True,
                "version": version,
                "database": settings.postgres_db,
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
