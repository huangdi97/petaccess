"""FastAPI application entrypoint (design #29, #31)."""

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings, validate_runtime
from app.core.errors import install_error_handlers
from app.core.observability import metrics, request_id_ctx
from app.db.session import check_db_health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # §75: a deployment missing its configuration must fail here, not degrade
    # into signing tokens with the key published in this repository.
    validate_runtime(get_settings())
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
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid
    request_id_ctx.set(rid)
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    route = request.scope.get("route")
    metric_name = f"http.{request.method}.{getattr(route, 'path', 'unknown')}"
    metrics.observe_latency(metric_name, time.monotonic() - start)
    metrics.incr("http.requests.total")
    if response.status_code >= 500:
        metrics.incr("http.requests.5xx")
    return response


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness: process is up."""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/health/database", tags=["health"])
async def health_database() -> dict:
    """Which database this process is really bound to.

    Exists because the E2E and visual suites must be able to *prove* the API they
    are talking to is not pointed at production. `reuseExistingServer` means a
    stray dev server on the expected port would otherwise serve the suite
    silently; this endpoint turns that into a hard failure in the global setup.

    Reads `current_database()` from the server rather than parsing the URL, and
    returns only the name and role — never the host, user or credentials.
    """
    from app.db.safety import classify_database_name, probe_database_name
    from app.db.session import get_engine

    name = probe_database_name(get_engine())
    return {
        "database": name,
        "role": classify_database_name(name).value,
        "app_env": settings.app_env,
    }


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict:
    """Readiness: DB/PostGIS reachable."""
    db = check_db_health()
    return {"status": "ready", "db": db}


@app.get("/health/components", tags=["health"])
async def health_components() -> dict:
    """Per-dependency health: DB/PostGIS, Redis, MinIO, Celery (NEXT_GOAL §A5)."""
    import redis as redis_lib

    from app.providers.factory import get_storage_provider
    from app.worker.celery_app import celery_app as celery

    components: dict[str, dict] = {}
    try:
        db = check_db_health()
        components["postgres"] = {"ok": True, "postgis": db["postgis"][:20]}
    except Exception as exc:
        components["postgres"] = {"ok": False, "error": str(exc)[:120]}
    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        components["redis"] = {"ok": bool(r.ping())}
    except Exception as exc:
        components["redis"] = {"ok": False, "error": str(exc)[:120]}
    try:
        components["minio"] = {"ok": bool(get_storage_provider().healthy())}
    except Exception as exc:
        components["minio"] = {"ok": False, "error": str(exc)[:120]}
    try:
        pings = celery.control.ping(timeout=2)
        components["celery"] = {"ok": bool(pings), "nodes": len(pings[0]) if pings else 0}
    except Exception as exc:
        components["celery"] = {"ok": False, "error": str(exc)[:120]}
    return {
        "components": components,
        "all_ok": all(c.get("ok") for c in components.values()),
    }


@app.get("/metrics", tags=["health"])
async def metrics_snapshot() -> dict:
    """In-process counters + latency percentiles (metrics abstraction)."""
    return metrics.snapshot()


app.include_router(api_router, prefix="/api/v1")
install_error_handlers(app)
