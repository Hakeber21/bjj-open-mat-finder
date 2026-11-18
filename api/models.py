"""
models.py — Pydantic response models.

These are used by the routers to serialise database rows into JSON.
Pydantic v2 handles datetime.time -> "HH:MM:SS" and
datetime.datetime -> ISO 8601 string automatically.
"""

from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# /api/search
# ---------------------------------------------------------------------------


class SearchResult(BaseModel):
    """One open_mat row joined to its gym, plus the computed distance."""

    # gym fields
    gym_id: int
    name: str
    address: Optional[str]
    city: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    website_url: Optional[str]
    instagram: Optional[str]
    visitor_policy: Optional[str]

    # open_mat fields
    open_mat_id: int
    day_of_week: Optional[int]
    start_time: datetime.time
    end_time: Optional[datetime.time]
    format: Optional[str]
    fee_cents: Optional[int]
    min_belt: Optional[str]
    notes: Optional[str]
    last_verified_at: Optional[datetime.datetime]
    verified_by: Optional[str]

    # computed
    distance_km: float


# ---------------------------------------------------------------------------
# /api/gyms/{id}
# ---------------------------------------------------------------------------


class OpenMatDetail(BaseModel):
    """An open_mat row nested inside a gym detail response."""

    id: int
    day_of_week: Optional[int]
    start_time: datetime.time
    end_time: Optional[datetime.time]
    format: Optional[str]
    fee_cents: Optional[int]
    min_belt: Optional[str]
    notes: Optional[str]
    last_verified_at: Optional[datetime.datetime]
    verified_by: Optional[str]


class GymDetail(BaseModel):
    """Full gym record with all its open_mat rows."""

    id: int
    name: str
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    website_url: Optional[str]
    instagram: Optional[str]
    source: str
    visitor_policy: Optional[str]
    created_at: Optional[datetime.datetime]
    open_mats: list[OpenMatDetail]
