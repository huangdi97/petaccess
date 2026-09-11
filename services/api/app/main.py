"""FastAPI application entrypoint (design #29, #31)."""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.db.session import check_db_health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


settings = get_settings()

app = FastAPI(
    title="Place Animal Access Map API",
    version="0.1.0",
    description="宠物准入信息平台 API — Place → Zone → AccessRule → deterministic evaluator.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:4173",
        "http://localhost:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness: process is up."""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict:
    """Readiness: DB/PostGIS reachable."""
    db = check_db_health()
    return {"status": "ready", "db": db}


app.include_router(api_router, prefix="/api/v1")
install_error_handlers(app)
