"""
Database connection and session management.
Uses SQLite with async support via aiosqlite + SQLAlchemy.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_DIR}/data.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency: yield an async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables and FTS5 index if they don't exist."""
    from models import Category, ApiEntry  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Create FTS5 virtual table for full-text search
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS api_fts USING fts5(
                name, provider, description, tags,
                content='api_entries',
                content_rowid='id'
            )
        """))

        # Populate FTS5 table (triggers would be better, but for simplicity rebuild periodically)
        await conn.execute(text("""
            INSERT INTO api_fts(api_fts) VALUES('rebuild')
        """))
