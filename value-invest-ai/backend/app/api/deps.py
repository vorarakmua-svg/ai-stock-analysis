"""
API Dependencies for FastAPI.

This module provides common dependencies used across API endpoints,
including database session injection and authentication.
"""

from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.

    Usage:
        @router.get("/items")
        async def get_items(db: DbSession):
            result = await db.execute(select(Item))
            return result.scalars().all()
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


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
