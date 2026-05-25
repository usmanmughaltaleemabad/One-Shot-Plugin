"""Async SQLAlchemy engine + session for the ride-sharing example.

Uses SQLite by default so the example runs without a real database.
Override via env var ``RIDESHARE_DB_URL`` for PostgreSQL etc.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DB_URL = os.environ.get("RIDESHARE_DB_URL", "sqlite+aiosqlite:///:memory:")

engine = create_async_engine(DB_URL, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a session."""
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create all tables. Used by tests and the demo run script."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
