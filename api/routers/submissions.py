"""
routers/submissions.py — POST /api/submissions

Accepts any JSON object and stores it in the submission table with
status='pending'.  Validation happens during human moderation, not here —
the payload schema evolves as the submission form does.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg.types.json import Jsonb

router = APIRouter()


def get_pool(request: Request):
    return request.app.state.pool


@router.post("/submissions", status_code=201)
async def create_submission(request: Request, pool=Depends(get_pool)):
    """
    Store a community submission for moderation.
    Returns {"status": "pending"} on success.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO submission (payload) VALUES (%s)",
                (Jsonb(payload),),
            )

    return {"status": "pending"}
