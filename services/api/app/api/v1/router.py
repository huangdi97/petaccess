"""API v1 aggregate router (design #31)."""

from fastapi import APIRouter

from . import (
    admin,
    ai,
    auth,
    disputes,
    media,
    observations,
    operators,
    pets,
    places,
    reality,
    regulations,
    rules,
    sources,
    v05,
    verifications,
    watches,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(pets.router)
api_router.include_router(places.router)
api_router.include_router(places.admin)
api_router.include_router(rules.router)
api_router.include_router(rules.admin)
api_router.include_router(sources.router)
api_router.include_router(sources.admin)
api_router.include_router(observations.router)
api_router.include_router(reality.router)
api_router.include_router(reality.admin)
api_router.include_router(verifications.router)
api_router.include_router(operators.router)
api_router.include_router(operators.admin)
api_router.include_router(regulations.router)
api_router.include_router(regulations.admin)
api_router.include_router(disputes.router)
api_router.include_router(disputes.admin)
api_router.include_router(watches.router)
api_router.include_router(media.router)
api_router.include_router(ai.router)
api_router.include_router(v05.router)
api_router.include_router(v05.admin)
api_router.include_router(admin.router)


@api_router.get("/ping", tags=["health"])
async def ping() -> dict:
    return {"pong": True}
