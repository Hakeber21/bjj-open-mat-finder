# ADR 0004 — API design

**Date:** 2026-11-17
**Status:** Accepted

## Context

We need a small HTTP API to serve the search query and gym detail to the
static frontend.  The choices below affect the developer experience, the
review surface, and the operational cost.

## Decisions

### FastAPI over Flask

FastAPI was chosen over Flask for three reasons:

1. **Native async.** FastAPI runs on ASGI (via Starlette), which pairs
   cleanly with psycopg3's async connection pool.  Flask's sync model would
   require threading or a separate async adapter.
2. **Automatic OpenAPI docs.** FastAPI generates a `/docs` Swagger UI and a
   `/redoc` page from the route signatures and Pydantic models at zero extra
   cost.  For a portfolio project this is a concrete deliverable.
3. **Pydantic validation at the boundary.** Query parameters and response
   shapes are declared as Pydantic types; FastAPI validates and serialises
   them automatically.  This keeps the route handlers thin and the
   validation logic reviewable.

Alternatives rejected: Flask (sync, no built-in validation), Django REST
Framework (heavy, overkill for a few endpoints).

### psycopg3 over psycopg2

psycopg3 (`psycopg` on PyPI) was chosen over psycopg2:

1. **Native async driver.** `psycopg3` ships `AsyncConnectionPool` and
   `AsyncConnection` as first-class types.  psycopg2 has no async support
   in its core; the common workaround is `aiopg` or `asyncpg`, which are
   separate packages with different APIs.
2. **Better type mapping.** psycopg3 maps Postgres `TIME` to
   `datetime.time`, `TIMESTAMPTZ` to `datetime.datetime`, and `BOOLEAN` to
   `bool` by default.  Pydantic then serialises those to `"HH:MM:SS"` and
   ISO 8601 strings without extra converters.
3. **Active maintenance.** psycopg2 is in maintenance mode; psycopg3 is the
   project's current focus.

Alternatives rejected: psycopg2 (no native async), asyncpg (different
parameter style and row API, no dict row factory by default).

### Plain Haversine with bounding-box pre-filter

This is consistent with ADR 0002 (schema design).  The key point for the
API layer is that the distance is computed inside a CTE so it can be aliased
and filtered in the outer `WHERE` clause without repeating the expression.

A `HAVING` clause on the raw `SELECT` would work too, but `HAVING` is
conventionally for aggregates; using a CTE with a plain `WHERE` on the alias
is more readable and makes the two-step logic (pre-filter, then exact
distance) explicit.

The bounding-box deltas are computed in Python before the query runs:

```python
lat_delta  = radius_km / 111.0
lng_delta  = radius_km / (111.0 * cos(radians(lat)))
```

These are passed as named parameters alongside the other query parameters.

### Why HAVING vs. WHERE — and why we chose neither directly

If the Haversine expression appeared directly in the `SELECT` list, a
`HAVING` clause on the alias would be needed because the expression is not
available to `WHERE` (which runs before projection).  However:

- `HAVING` without `GROUP BY` is a Postgres extension; it is valid but
  surprising to readers.
- Repeating the full Haversine expression in `HAVING` is noisy and error-
  prone.

The CTE approach aliases the distance in the inner query, then the outer
query filters on the alias with a plain `WHERE`.  This is standard SQL,
easy to follow, and separates the "compute candidates" step from the
"apply distance cutoff" step visually.

## Alternatives rejected

| Alternative | Reason rejected |
|---|---|
| `HAVING` clause on the main `SELECT` | Non-aggregate `HAVING` is non-standard and harder to read |
| Repeat Haversine in `WHERE` and `SELECT` | Duplication; two places to update if the formula changes |
| PostGIS `ST_DWithin` | Extension availability not guaranteed on free tiers (see ADR 0002) |
| Subquery instead of CTE | CTE is easier to read and label; equivalent performance for this size |
