"""
Async SQLAlchemy engine + session factory (PostgreSQL via asyncpg).
Swap DATABASE_URL for a Mongo/Motor setup if you prefer NoSQL —
see db/mongo.py for the alternative (kept side by side, unused by default).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables on startup (use Alembic migrations in real production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
