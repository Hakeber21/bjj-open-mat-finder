"""
main.py — FastAPI application entry point.

Start for development:
    python3 -m uvicorn api.main:app --reload

Reads DATABASE_URL from the environment; if a .env file is present in the
working directory, python-dotenv loads it before the pool is created.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db import create_pool
from api.routers import gyms, search, submissions

# Load env files. .env.local (Neon-generated) takes precedence over .env.
# Both are gitignored; .env.example is the committed template.
load_dotenv()
load_dotenv(".env.local", override=True)


# ---------------------------------------------------------------------------
# Lifespan: open pool on startup, close on shutdown.
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BJJ Open Mat Finder API",
    description=(
        "Find BJJ open mat sessions near a location. "
        "Launch region: Austin, TX. Source: openmat.hirebekah.com"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# TODO: Tighten this to the production origin before launch.
#       For MVP, allow all origins because the frontend is a static page
#       served from a different domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(search.router, prefix="/api")
app.include_router(gyms.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")


@app.get("/health", tags=["ops"])
async def health():
    """Liveness check. No DB call — just confirms the process is up."""
    return {"status": "ok"}
