"""
db.py — async connection pool for psycopg3.

The pool is opened once at startup (via FastAPI's lifespan) and stored on
app.state so every request can borrow a connection without paying the
connect overhead.

Neon provides two URLs:
  DATABASE_URL_UNPOOLED  — direct connection; use this with psycopg3's own
                           pool to avoid double-pooling with Neon's PgBouncer.
  DATABASE_URL           — Neon's PgBouncer pooler; preferred for serverless
                           runtimes that cannot hold open connections.

We use the unpooled URL here and let psycopg3 manage the pool.
"""

import os

from psycopg_pool import AsyncConnectionPool


def _get_database_url() -> str:
    # Prefer the unpooled URL to avoid double-pooling with Neon's PgBouncer.
    url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL_UNPOOLED (or DATABASE_URL) is not set. "
            "Run `neon deploy` to populate .env.local, or copy .env.example to .env."
        )
    return url


async def create_pool() -> AsyncConnectionPool:
    """Open the connection pool.  Call once at application startup."""
    url = _get_database_url()
    # min_size=1 keeps one warm connection; max_size=5 is generous for a
    # free-tier DB that limits concurrent connections.
    pool = AsyncConnectionPool(conninfo=url, min_size=1, max_size=5, open=False)
    await pool.open()
    return pool
