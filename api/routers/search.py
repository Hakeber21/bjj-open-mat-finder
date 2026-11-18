"""
routers/search.py — GET /api/search

Returns open mat sessions within a radius of a lat/lng point, with optional
filters for day, format, visitor policy, and free-only sessions.

The core query uses plain-SQL Haversine with a bounding-box pre-filter
(see ADRs 0002 and 0004 for the rationale).

All filter values come from FastAPI's Query() validator, never from
string formatting — parameterised queries only.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg.rows import dict_row

from api.models import SearchResult

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency: pull the connection pool off app.state
# ---------------------------------------------------------------------------


def get_pool(request: Request):
    return request.app.state.pool


# ---------------------------------------------------------------------------
# Core SQL
#
# Strategy: wrap the Haversine expression in a CTE so we can give it an
# alias ("distance_km") and filter on that alias in a WHERE clause instead
# of repeating the expression in a HAVING clause.  This is cleaner and
# avoids the HAVING-without-GROUP-BY ambiguity.
#
# Bounding-box pre-filter narrows the scan to a rough square first, then
# the Haversine in the outer WHERE discards corners.  The (lat, lng) index
# on gym powers the pre-filter.
#
# Parameter style: %(name)s  (psycopg3 default for dict params).
# ---------------------------------------------------------------------------

_SEARCH_SQL = """
WITH candidates AS (
    SELECT
        g.id          AS gym_id,
        g.name,
        g.address,
        g.city,
        g.lat,
        g.lng,
        g.website_url,
        g.instagram,
        g.visitor_policy,
        om.id         AS open_mat_id,
        om.day_of_week,
        om.start_time,
        om.end_time,
        om.format,
        om.fee_cents,
        om.min_belt,
        om.notes,
        om.last_verified_at,
        om.verified_by,
        -- Haversine distance in km between the user's point and the gym.
        -- 6371 is the mean Earth radius in km.
        6371.0 * 2.0 * ASIN(SQRT(
            POWER(SIN(RADIANS(g.lat - %(lat)s) / 2.0), 2) +
            COS(RADIANS(%(lat)s)) * COS(RADIANS(g.lat)) *
            POWER(SIN(RADIANS(g.lng - %(lng)s) / 2.0), 2)
        )) AS distance_km
    FROM open_mat om
    JOIN gym g ON g.id = om.gym_id
    WHERE
        -- Bounding-box pre-filter uses the idx_gym_lat_lng index.
        -- lat_delta  = radius_km / 111.0  (1 degree lat ≈ 111 km)
        -- lng_delta  = radius_km / (111.0 * cos(lat))
        g.lat  BETWEEN %(lat)s  - %(lat_delta)s  AND %(lat)s  + %(lat_delta)s
        AND g.lng BETWEEN %(lng)s  - %(lng_delta)s AND %(lng)s  + %(lng_delta)s
        -- Skip gyms with no coordinates; they can never appear on a map.
        AND g.lat  IS NOT NULL
        AND g.lng  IS NOT NULL
        -- Optional day-of-week filter (NULL means "any day").
        AND (%(day)s::smallint         IS NULL OR om.day_of_week = %(day)s::smallint)
        -- Optional format filter (NULL means "any format").
        AND (%(format)s::text          IS NULL OR om.format      = %(format)s::text)
        -- Optional visitor policy filter.
        AND (%(visitor_policy)s::text  IS NULL OR g.visitor_policy = %(visitor_policy)s::text)
        -- Free-only filter: only include rows where fee is explicitly 0.
        -- NULL fee (unknown cost) is excluded when free_only is true.
        AND (NOT %(free_only)s         OR om.fee_cents = 0)
)
SELECT *
FROM   candidates
WHERE  distance_km <= %(radius_km)s
ORDER BY last_verified_at DESC NULLS LAST,
         distance_km       ASC;
"""


@router.get("/search", response_model=list[SearchResult])
async def search_open_mats(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(25.0, gt=0, le=200, description="Search radius in km"),
    day: Optional[int] = Query(None, ge=1, le=7, description="ISO day of week (1=Mon, 7=Sun)"),
    format: Optional[str] = Query(None, pattern="^(gi|nogi|both)$", description="gi, nogi, or both"),
    visitor_policy: Optional[str] = Query(
        None,
        pattern="^(welcome|call_first|members_only|unknown)$",
        description="visitor policy filter",
    ),
    free_only: bool = Query(False, description="Only return sessions where fee_cents = 0"),
    pool=Depends(get_pool),
):
    """
    Return open mat sessions within radius_km of (lat, lng).

    Results are ordered by freshness (most recently verified first),
    then by distance ascending.  Gyms with no coordinates are excluded.
    """
    # Validate lat/lng ranges.
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=422, detail="lat must be between -90 and 90")
    if not (-180 <= lng <= 180):
        raise HTTPException(status_code=422, detail="lng must be between -180 and 180")

    # Bounding-box deltas.  Guard against cos(lat) approaching zero near
    # the poles (not relevant for Austin, but correct for general use).
    lat_delta = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    # Clamp to avoid division by zero within a few metres of the poles.
    cos_lat = max(cos_lat, 1e-9)
    lng_delta = radius_km / (111.0 * cos_lat)

    params = {
        "lat": lat,
        "lng": lng,
        "radius_km": radius_km,
        "lat_delta": lat_delta,
        "lng_delta": lng_delta,
        "day": day,
        "format": format,
        "visitor_policy": visitor_policy,
        "free_only": free_only,
    }

    async with pool.connection() as conn:
        # dict_row is psycopg3's built-in row factory; each row comes back as
        # a plain dict keyed by column name, which Pydantic can unpack directly.
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(_SEARCH_SQL, params)
            rows = await cur.fetchall()

    return [SearchResult(**row) for row in rows]
