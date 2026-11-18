"""
test_gyms.py — tests for GET /api/gyms/{id}

Tests cover:
  - happy path: gym found with open mats
  - gym with no open mats
  - gym not found (404)
  - gym with NULL coordinates (still returns, coords are optional)
  - open mat with unknown fee (fee_cents=NULL)
  - open mat with stale last_verified_at (NULL)
"""

from __future__ import annotations

import datetime

import pytest

from api.routers.gyms import get_pool
from api.main import app
from tests.conftest import FakePool, FakeConnection, FakeCursor, make_gym_row, make_open_mat_row


class FakeTwoQueryPool:
    """
    A pool that serves two sequential queries: first the gym row, then the
    open_mat rows.  This mirrors the two .execute() calls in get_gym().
    """

    def __init__(self, gym_rows: list[dict], open_mat_rows: list[dict]):
        self._gym_rows = gym_rows
        self._open_mat_rows = open_mat_rows

    def connection(self):
        return _TwoQueryConnection(self._gym_rows, self._open_mat_rows)


class _TwoQueryConnection:
    def __init__(self, gym_rows, open_mat_rows):
        self._gym_rows = gym_rows
        self._open_mat_rows = open_mat_rows

    def cursor(self, row_factory=None):
        return _TwoQueryCursor(self._gym_rows, self._open_mat_rows)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class _TwoQueryCursor:
    """Cursor that cycles through two result sets on successive execute() calls."""

    def __init__(self, gym_rows, open_mat_rows):
        self._results = [gym_rows, open_mat_rows]
        self._call_count = 0
        self._current_rows: list[dict] = []

    async def execute(self, sql, params=None):
        self._current_rows = self._results[self._call_count]
        self._call_count += 1

    async def fetchone(self) -> dict | None:
        if self._current_rows:
            return self._current_rows[0]
        return None

    async def fetchall(self) -> list[dict]:
        return list(self._current_rows)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def _override_pool(gym_rows, open_mat_rows=()):
    def _dep():
        return FakeTwoQueryPool(gym_rows, list(open_mat_rows))
    return _dep


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_gym_with_open_mats(client):
    """Gym found with open mats returns full detail."""
    gym = make_gym_row()
    om = make_open_mat_row()
    app.dependency_overrides[get_pool] = _override_pool([gym], [om])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Test Gym"
    assert data["source"] == "osm"
    assert len(data["open_mats"]) == 1
    assert data["open_mats"][0]["id"] == 10
    assert data["open_mats"][0]["start_time"] == "10:00:00"
    assert data["open_mats"][0]["fee_cents"] == 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_gym_no_open_mats(client):
    """Gym found but no open mats returns empty list."""
    gym = make_gym_row()
    app.dependency_overrides[get_pool] = _override_pool([gym], [])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    assert resp.json()["open_mats"] == []

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_gym_not_found_returns_404(client):
    """Gym not found returns 404."""
    app.dependency_overrides[get_pool] = _override_pool([], [])

    resp = await client.get("/api/gyms/999")
    assert resp.status_code == 404

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_gym_null_coordinates(client):
    """
    A gym with no coordinates (lat=None, lng=None) is still returned.
    Missing coords are allowed in the schema; we just can't put it on a map.
    """
    gym = make_gym_row(lat=None, lng=None)
    app.dependency_overrides[get_pool] = _override_pool([gym], [])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lat"] is None
    assert data["lng"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_gym_open_mat_unknown_fee(client):
    """
    fee_cents=None (unknown) must serialise to null, not 0.
    NULL = we don't know the cost; 0 = explicitly free.
    """
    gym = make_gym_row()
    om = make_open_mat_row(fee_cents=None)
    app.dependency_overrides[get_pool] = _override_pool([gym], [om])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    assert resp.json()["open_mats"][0]["fee_cents"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_gym_open_mat_stale_verified_at(client):
    """
    last_verified_at=None (never verified) serialises to null.
    verified_by=None also serialises to null.
    """
    gym = make_gym_row()
    om = make_open_mat_row(last_verified_at=None, verified_by=None)
    app.dependency_overrides[get_pool] = _override_pool([gym], [om])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    om_resp = resp.json()["open_mats"][0]
    assert om_resp["last_verified_at"] is None
    assert om_resp["verified_by"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_gym_multiple_open_mats(client):
    """Multiple open_mat rows are all returned and ordered by day."""
    gym = make_gym_row()
    om1 = make_open_mat_row(id=1, day_of_week=6, start_time=datetime.time(10, 0))
    om2 = make_open_mat_row(id=2, day_of_week=7, start_time=datetime.time(11, 0))
    # Fake DB returns them in the right order already (SQL would sort them).
    app.dependency_overrides[get_pool] = _override_pool([gym], [om1, om2])

    resp = await client.get("/api/gyms/1")
    assert resp.status_code == 200
    open_mats = resp.json()["open_mats"]
    assert len(open_mats) == 2
    assert open_mats[0]["id"] == 1
    assert open_mats[1]["id"] == 2

    app.dependency_overrides.clear()
