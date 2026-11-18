"""
routers/gyms.py — GET /api/gyms/{id}

Returns the full gym record plus all its open_mat rows.
Returns 404 if no gym exists with that id.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg.rows import dict_row

from api.models import GymDetail, OpenMatDetail

router = APIRouter()


def get_pool(request: Request):
    return request.app.state.pool


# Fetch the gym row.
_GYM_SQL = """
SELECT
    id,
    name,
    address,
    city,
    country,
    lat,
    lng,
    website_url,
    instagram,
    source,
    visitor_policy,
    created_at
FROM gym
WHERE id = %(gym_id)s;
"""

# Fetch all open_mat rows for the gym, ordered by day then start time.
_OPEN_MATS_SQL = """
SELECT
    id,
    day_of_week,
    start_time,
    end_time,
    format,
    fee_cents,
    min_belt,
    notes,
    last_verified_at,
    verified_by
FROM open_mat
WHERE gym_id = %(gym_id)s
ORDER BY day_of_week ASC NULLS LAST, start_time ASC;
"""


@router.get("/gyms/{gym_id}", response_model=GymDetail)
async def get_gym(gym_id: int, pool=Depends(get_pool)):
    """
    Return full gym detail with all its open mat sessions.
    404 if the gym does not exist.
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # Fetch the gym.
            await cur.execute(_GYM_SQL, {"gym_id": gym_id})
            gym_row = await cur.fetchone()

            if gym_row is None:
                raise HTTPException(status_code=404, detail="Gym not found")

            # Fetch all open mats for this gym.
            await cur.execute(_OPEN_MATS_SQL, {"gym_id": gym_id})
            open_mat_rows = await cur.fetchall()

    open_mats = [OpenMatDetail(**row) for row in open_mat_rows]
    return GymDetail(**gym_row, open_mats=open_mats)
