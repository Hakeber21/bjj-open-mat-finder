"""
conftest.py — shared fixtures for the test suite.

The tests use httpx's AsyncClient against the FastAPI app with a fake
pool injected via dependency_overrides.  No real database connection is
needed: each test supplies the rows the fake cursor will return.

Pattern:
  1. Build a list of row dicts (what the real DB would return).
  2. Wrap them in FakeCursor / FakePool.
  3. Override app.dependency_overrides[get_pool] with a function that
     returns FakePool.
  4. Make the request; assert on the JSON response.
"""

from __future__ import annotations

import datetime
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app


# ---------------------------------------------------------------------------
# Minimal fake psycopg3 pool / cursor
# ---------------------------------------------------------------------------


class FakeCursor:
    """
    Minimal async cursor that serves a pre-defined list of row dicts.
    The row_factory argument is accepted but ignored; we return dicts directly.
    """

    def __init__(self, rows: list[dict]):
        self._rows = rows
        self._one_consumed = False

    async def execute(self, sql, params=None):
        # No-op: rows are fixed at construction time.
        pass

    async def fetchall(self) -> list[dict]:
        return list(self._rows)

    async def fetchone(self) -> dict | None:
        if self._rows:
            return self._rows[0]
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeConnection:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def cursor(self, row_factory=None):
        # Return the fake cursor regardless of row_factory.
        return FakeCursor(self._rows)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakePool:
    """
    Fake pool whose .connection() context manager yields a FakeConnection
    with the supplied rows.
    """

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def connection(self):
        return FakeConnection(self._rows)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client pointed at the FastAPI app.
    The lifespan (which opens a real DB pool) is bypassed by using
    app directly; tests inject their own pool via dependency_overrides.

    We set a sentinel on app.state.pool so the get_pool() dependency
    function does not raise AttributeError in tests that expect a 422
    before the pool is ever used (FastAPI resolves all dependencies
    before validating some parameters, depending on dependency order).
    Tests that need a real fake pool add their own override.
    """
    app.state.pool = None  # sentinel; overridden per-test where needed
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
    # Clean up the sentinel so it does not leak between test runs.
    if hasattr(app.state, "pool"):
        del app.state._state["pool"]


def make_search_row(
    *,
    gym_id: int = 1,
    name: str = "Test Gym",
    address: str | None = "123 Main St",
    city: str | None = "Austin",
    lat: float | None = 30.267,
    lng: float | None = -97.743,
    website_url: str | None = None,
    instagram: str | None = None,
    visitor_policy: str | None = "welcome",
    open_mat_id: int = 10,
    day_of_week: int | None = 6,
    start_time: datetime.time = datetime.time(10, 0),
    end_time: datetime.time | None = datetime.time(12, 0),
    format: str | None = "nogi",
    fee_cents: int | None = 0,
    min_belt: str | None = None,
    notes: str | None = None,
    last_verified_at: datetime.datetime | None = None,
    verified_by: str | None = None,
    distance_km: float = 1.4,
) -> dict:
    """Build a search result row dict with sensible defaults."""
    return {
        "gym_id": gym_id,
        "name": name,
        "address": address,
        "city": city,
        "lat": lat,
        "lng": lng,
        "website_url": website_url,
        "instagram": instagram,
        "visitor_policy": visitor_policy,
        "open_mat_id": open_mat_id,
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
        "format": format,
        "fee_cents": fee_cents,
        "min_belt": min_belt,
        "notes": notes,
        "last_verified_at": last_verified_at,
        "verified_by": verified_by,
        "distance_km": distance_km,
    }


def make_gym_row(
    *,
    id: int = 1,
    name: str = "Test Gym",
    address: str | None = "123 Main St",
    city: str | None = "Austin",
    country: str | None = "US",
    lat: float | None = 30.267,
    lng: float | None = -97.743,
    website_url: str | None = None,
    instagram: str | None = None,
    source: str = "osm",
    visitor_policy: str | None = "welcome",
    created_at: datetime.datetime | None = None,
) -> dict:
    return {
        "id": id,
        "name": name,
        "address": address,
        "city": city,
        "country": country,
        "lat": lat,
        "lng": lng,
        "website_url": website_url,
        "instagram": instagram,
        "source": source,
        "visitor_policy": visitor_policy,
        "created_at": created_at,
    }


def make_open_mat_row(
    *,
    id: int = 10,
    day_of_week: int | None = 6,
    start_time: datetime.time = datetime.time(10, 0),
    end_time: datetime.time | None = datetime.time(12, 0),
    format: str | None = "nogi",
    fee_cents: int | None = 0,
    min_belt: str | None = None,
    notes: str | None = None,
    last_verified_at: datetime.datetime | None = None,
    verified_by: str | None = None,
) -> dict:
    return {
        "id": id,
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
        "format": format,
        "fee_cents": fee_cents,
        "min_belt": min_belt,
        "notes": notes,
        "last_verified_at": last_verified_at,
        "verified_by": verified_by,
    }
