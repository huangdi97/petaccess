"""Observation endpoints (design #14, #15, #31).

Observations are parallel facts: creating one NEVER mutates rules (ADR-004).
Raw GPS is never persisted — only client-bucketed proximity data (ADR-012).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFound, PermissionDenied
from app.core.idempotency import check_inflight, get_cached, store
from app.core.ratelimit import check_rate_limit
from app.core.security import get_current_user, get_optional_user
from app.db.session import get_db
from app.models import ObservationClaim, Place, User
from app.schemas.civic import ObservationIn, ObservationOut
from app.schemas.common import Page

router = APIRouter(tags=["observations"])


@router.get("/places/{place_id}/observations", response_model=Page[ObservationOut])
def list_place_observations(
    place_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[ObservationOut]:
    stmt = (
        select(ObservationClaim)
        .where(
            ObservationClaim.place_id == place_id,
            ObservationClaim.withdrawn_at.is_(None),
            ObservationClaim.dispute_status != "open",
        )
        .order_by(ObservationClaim.reported_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.post("/observations", response_model=ObservationOut, status_code=201)
def create_observation(
    body: ObservationIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObservationClaim:
    settings = get_settings()
    check_rate_limit(
        "observations",
        user.id,
        settings.observation_rate_max,
        settings.observation_rate_window_seconds,
    )
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    idem_key = request.headers.get("Idempotency-Key", "")
    if idem_key:
        cached = get_cached("observation", idem_key)
        if cached is not None:
            obs = db.get(ObservationClaim, cached["id"])
            if obs is not None:
                return obs
        check_inflight("observation", idem_key)
    data = body.model_dump()
    evidence = data.pop("evidence_refs", None)
    obs = ObservationClaim(
        **data,
        evidence_support=evidence,
        user_id=user.id,
        reported_at=datetime.now(UTC),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    if idem_key:
        store("observation", idem_key, {"id": obs.id})
    return obs


@router.post("/observations/{observation_id}/withdraw", response_model=ObservationOut)
def withdraw_observation(
    observation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObservationClaim:
    obs = db.get(ObservationClaim, observation_id)
    if obs is None:
        raise NotFound("观察记录不存在")
    if obs.user_id != user.id and user.role not in ("moderator", "admin"):
        raise PermissionDenied("只能撤回自己的观察记录")
    if obs.withdrawn_at is None:
        obs.withdrawn_at = datetime.now(UTC)
        db.commit()
        db.refresh(obs)
    return obs
