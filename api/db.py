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
    # Neon (our Postgres host) is "serverless": after a few minutes of no
    # queries it auto-suspends the database, and on suspend it drops every open
    # connection. A connection pool that doesn't account for this will hand a
    # request a connection Neon has already killed, and that request fails with:
    #   psycopg.errors.AdminShutdown: terminating connection due to
    #   administrator command
    # ...then succeeds on retry. The two settings below prevent that.
    #
    # check=AsyncConnectionPool.check_connection -- the important one. Before the
    #   pool gives a connection to a request, it runs this quick liveness check
    #   and transparently replaces the connection if Neon has closed it. This is
    #   what actually stops the "first request after idle" 500s: callers never
    #   receive a dead connection. (Cost: one tiny round-trip per checkout.)
    #
    # min_size=0 -- how many connections the pool holds open while idle. We keep
    #   zero: a warm connection to a suspended Neon is just a dead connection
    #   waiting to be discarded, so there's no point holding one. The pool still
    #   opens connections on demand, up to max_size. (On its own min_size=0 is
    #   NOT enough -- a connection returned to the pool can still sit idle past
    #   Neon's suspend window; that's exactly why we also need the check above.)
    #
    # max_size=5 -- a safe ceiling for Neon free tier's connection limit.
    pool = AsyncConnectionPool(
        conninfo=url,
        min_size=0,
        max_size=5,
        check=AsyncConnectionPool.check_connection,
        open=False,
    )
    await pool.open()
    return pool
