"""
Database configuration and session management.

This module provides database connection setup using SQLAlchemy 2.0 async style
with asyncpg driver for PostgreSQL.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .config import settings


# Construct database URL from individual parameters
# Workaround for asyncpg DNS resolution issue in Kubernetes
database_url = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.ENVIRONMENT == "development",  # Log SQL in development
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,  # Disable pooling in tests
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual control over flushing
    autocommit=False,  # Explicit transaction management
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to provide database sessions.

    Yields:
        AsyncSession instance

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db session
            pass

    Note:
        Automatically handles session lifecycle:
        - Creates session at request start
        - Commits on success
        - Rolls back on exception
        - Closes session at request end
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database (create tables).

    Note:
        In production, use Alembic migrations instead of this.
        This is useful for development and testing.
    """
    from .models.session import Base  # Import Base from models

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections (cleanup on shutdown).
    """
    await engine.dispose()
