"""
test_search.py — tests for GET /api/search

Tests cover:
  - happy path: results returned and serialised correctly
  - empty result: no open mats near the point
  - optional filters: day, format, visitor_policy, free_only
  - edge cases: unknown fee (NULL), missing coordinates, stale listing
  - validation errors: missing lat/lng, bad day, bad format
  - ordering: freshest first, then nearest
"""

from __future__ import annotations

import datetime

import pytest

from api.routers.search import get_pool
from api.main import app
from tests.conftest import FakePool, make_search_row


def _override_pool(rows):
    """Return a FastAPI dependency override that injects a FakePool."""

    def _pool_dep():
        return FakePool(rows)

    return _pool_dep


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_results(client):
    """A well-formed search with matching rows returns serialised results."""
    row = make_search_row()
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    result = data[0]
    assert result["gym_id"] == 1
    assert result["name"] == "Test Gym"
    assert result["distance_km"] == 1.4
    assert result["start_time"] == "10:00:00"
    assert result["fee_cents"] == 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_empty_result(client):
    """When the DB returns no rows, the response is an empty list."""
    app.dependency_overrides[get_pool] = _override_pool([])

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    assert resp.json() == []

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Optional filters are forwarded (they reach the SQL via params)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_day_filter_accepted(client):
    """day parameter in range 1–7 is accepted and returns results."""
    row = make_search_row(day_of_week=6)
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get(
        "/api/search", params={"lat": 30.267, "lng": -97.743, "day": 6}
    )
    assert resp.status_code == 200
    assert resp.json()[0]["day_of_week"] == 6

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_format_filter_accepted(client):
    """format=nogi is accepted and the response echoes the format field."""
    row = make_search_row(format="nogi")
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get(
        "/api/search", params={"lat": 30.267, "lng": -97.743, "format": "nogi"}
    )
    assert resp.status_code == 200
    assert resp.json()[0]["format"] == "nogi"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_visitor_policy_filter_accepted(client):
    """visitor_policy=welcome is accepted."""
    row = make_search_row(visitor_policy="welcome")
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get(
        "/api/search",
        params={"lat": 30.267, "lng": -97.743, "visitor_policy": "welcome"},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["visitor_policy"] == "welcome"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_free_only_accepted(client):
    """free_only=true is accepted; results with fee_cents=0 are returned."""
    row = make_search_row(fee_cents=0)
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get(
        "/api/search",
        params={"lat": 30.267, "lng": -97.743, "free_only": "true"},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["fee_cents"] == 0

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Edge case: unknown fee (fee_cents = NULL)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_unknown_fee_serialises_as_null(client):
    """
    fee_cents=None (DB NULL) must serialise to JSON null, not 0.
    NULL means the fee is unknown — it must not be confused with free.
    """
    row = make_search_row(fee_cents=None)
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    assert resp.json()[0]["fee_cents"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_free_only_excludes_unknown_fee(client):
    """
    free_only=true must not return rows where fee_cents is NULL (unknown).
    The SQL WHERE clause handles this, but verify the endpoint accepts the
    flag and that an unknown-fee row is absent when it is the only result.
    The fake DB returns no rows, simulating what the SQL would do.
    """
    # Fake DB returns empty — the SQL filtered out the NULL-fee row.
    app.dependency_overrides[get_pool] = _override_pool([])

    resp = await client.get(
        "/api/search",
        params={"lat": 30.267, "lng": -97.743, "free_only": "true"},
    )
    assert resp.status_code == 200
    assert resp.json() == []

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Edge case: missing coordinates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_gym_missing_coords_excluded(client):
    """
    The SQL WHERE clause excludes gyms with NULL lat/lng, so the fake DB
    returns no rows.  The endpoint should still return 200 [].
    """
    app.dependency_overrides[get_pool] = _override_pool([])

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    assert resp.json() == []

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Edge case: stale listing (last_verified_at = NULL)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_stale_listing_serialises_null_verified_at(client):
    """
    A listing with no verification date (last_verified_at=None) is included
    in results but its last_verified_at field serialises to null.
    The ORDER BY sorts NULLs last, so stale rows appear at the bottom.
    """
    row = make_search_row(last_verified_at=None, verified_by=None)
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    result = resp.json()[0]
    assert result["last_verified_at"] is None
    assert result["verified_by"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_freshness_ordering(client):
    """
    Results should be ordered by last_verified_at DESC NULLS LAST.
    The fake DB returns rows in this order (the SQL would have sorted them);
    verify the response preserves the order.
    """
    now = datetime.datetime(2026, 11, 17, 12, 0, 0)
    yesterday = datetime.datetime(2026, 11, 16, 12, 0, 0)

    fresh_row = make_search_row(open_mat_id=1, last_verified_at=now, distance_km=2.0)
    stale_row = make_search_row(open_mat_id=2, last_verified_at=yesterday, distance_km=1.0)
    # Note: stale_row is closer but fresher row comes first (freshness wins).
    unverified_row = make_search_row(open_mat_id=3, last_verified_at=None, distance_km=0.5)

    rows = [fresh_row, stale_row, unverified_row]
    app.dependency_overrides[get_pool] = _override_pool(rows)

    resp = await client.get("/api/search", params={"lat": 30.267, "lng": -97.743})
    assert resp.status_code == 200
    ids = [r["open_mat_id"] for r in resp.json()]
    assert ids == [1, 2, 3]  # fresh, stale, then unverified (nulls last)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Multiple results with radius filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_custom_radius(client):
    """radius_km parameter is forwarded to the query (fake DB returns a row)."""
    row = make_search_row(distance_km=10.0)
    app.dependency_overrides[get_pool] = _override_pool([row])

    resp = await client.get(
        "/api/search", params={"lat": 30.267, "lng": -97.743, "radius_km": 15}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_missing_lat_returns_422(client):
    """lat is required; omitting it must return 422."""
    resp = await client.get("/api/search", params={"lng": -97.743})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_missing_lng_returns_422(client):
    """lng is required; omitting it must return 422."""
    resp = await client.get("/api/search", params={"lat": 30.267})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_bad_day_returns_422(client):
    """day must be 1–7; 0 and 8 must return 422."""
    for bad_day in (0, 8, -1):
        resp = await client.get(
            "/api/search", params={"lat": 30.267, "lng": -97.743, "day": bad_day}
        )
        assert resp.status_code == 422, f"expected 422 for day={bad_day}"


@pytest.mark.asyncio
async def test_search_bad_format_returns_422(client):
    """format must be gi, nogi, or both; anything else returns 422."""
    resp = await client.get(
        "/api/search", params={"lat": 30.267, "lng": -97.743, "format": "wrestling"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_bad_visitor_policy_returns_422(client):
    """visitor_policy must be one of the four allowed values."""
    resp = await client.get(
        "/api/search",
        params={"lat": 30.267, "lng": -97.743, "visitor_policy": "maybe"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_lat_out_of_range_returns_422(client):
    """lat > 90 or lat < -90 must return 422."""
    for bad_lat in (91.0, -91.0):
        # FastAPI does not validate lat range via Query bounds, so our
        # explicit check in the route handler raises a 422.
        app.dependency_overrides[get_pool] = _override_pool([])
        resp = await client.get(
            "/api/search", params={"lat": bad_lat, "lng": -97.743}
        )
        assert resp.status_code == 422, f"expected 422 for lat={bad_lat}"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_zero_radius_returns_422(client):
    """radius_km must be > 0; passing 0 returns 422."""
    resp = await client.get(
        "/api/search", params={"lat": 30.267, "lng": -97.743, "radius_km": 0}
    )
    assert resp.status_code == 422
