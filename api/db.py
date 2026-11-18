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
    # min_size = the number of connections the pool keeps open even when idle.
    # We set it to 0 because Neon is "serverless": it auto-suspends the database
    # when nothing is querying it, and on suspend it drops any open connection.
    # So holding a warm connection (min_size=1) buys little here, and a held
    # connection can quietly go stale after a suspend -- the next request would
    # then hit a dead connection and error once before reconnecting.
    # With min_size=0 the pool holds nothing while idle and opens a fresh
    # connection on the first request after a quiet spell (a small one-time
    # "cold start"), so it never hands out a dead connection.
    # max_size=5 is the ceiling: at most 5 connections at once, which is kind to
    # the free tier's connection limit. Steady traffic still reuses warm
    # connections normally; only the first request after an idle gap pays extra.
    pool = AsyncConnectionPool(conninfo=url, min_size=0, max_size=5, open=False)
    await pool.open()
    return pool
