"""
Configuration de la base de donnees PostgreSQL (asyncpg).

Cree le moteur SQLAlchemy async et la factory de sessions.
La fonction get_session() est utilisee comme dependance FastAPI
pour injecter une session dans chaque endpoint.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import structlog

from app.core.config import settings

logger = structlog.get_logger()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,   # detect & replace stale connections (e.g. after a PG restart)
    pool_recycle=1800,    # recycle connections every 30 min (avoids proxy idle drops)
    pool_size=10,
    max_overflow=20,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database initialized")


async def get_session() -> AsyncSession:
    """Get database session, rolling back on unhandled exceptions."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
