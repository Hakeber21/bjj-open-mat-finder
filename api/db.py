"""
db.py — async connection pool for psycopg3.

The pool is opened once at startup (via FastAPI's lifespan) and stored on
app.state so every request can borrow a connection without paying the
connect overhead.

DATABASE_URL is read from the environment.  If a .env file is present,
python-dotenv loads it before this module is imported (see main.py).

psycopg3 connection string format:
    postgresql+psycopg://user:password@host:5432/dbname
The "postgresql+psycopg" scheme is recognised by psycopg3; plain
"postgresql" also works.
"""

import os

from psycopg_pool import AsyncConnectionPool


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Copy .env.example to .env and fill it in."
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
