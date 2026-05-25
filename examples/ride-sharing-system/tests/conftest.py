"""Shared fixtures: in-memory DB, FastAPI test client."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the example's app package is importable when pytest is invoked
# from the repo root with: pytest examples/ride-sharing-system/tests
EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
if str(EXAMPLE_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_ROOT))

# Use a fresh in-memory DB per test session. SQLite ":memory:" with the
# async driver shares one database per engine, which is exactly what we want.
os.environ.setdefault("RIDESHARE_DB_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db import Base, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _fresh_schema():
    """Drop and recreate every table between tests so each test is hermetic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def passenger_registration() -> dict:
    return {
        "email": "rider@example.com",
        "phone": "+15551112222",
        "password": "rider-secret-pw",
        "full_name": "Rider One",
        "role": "passenger",
    }


@pytest.fixture
def driver_registration() -> dict:
    return {
        "email": "driver@example.com",
        "phone": "+15553334444",
        "password": "driver-secret-pw",
        "full_name": "Driver One",
        "role": "driver",
    }
