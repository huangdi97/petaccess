"""API v1 aggregate router. Routers are registered as phases land."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/ping", tags=["health"])
async def ping() -> dict:
    return {"pong": True}
