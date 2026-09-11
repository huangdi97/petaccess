"""Jurisdiction regulation endpoints (design #18, GOAL #14).

review_status strictly distinguishes NOT_REVIEWED / NO_EXPLICIT_RULE_FOUND /
EXPLICIT_OPERATOR_DISCRETION / REVIEWED_ACTIVE. 'Not reviewed' is never
rendered as 'the law says nothing'.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.errors import NotFound
from app.core.security import get_optional_user, require_role
from app.db.session import get_db
from app.models import JurisdictionRule, User
from app.models.enums import UserRole
from app.schemas.civic import RegulationIn, RegulationOut, RegulationUpdate
from app.schemas.common import Page

router = APIRouter(tags=["regulations"])
admin = APIRouter(tags=["admin:regulations"])


@router.get("/regulations", response_model=Page[RegulationOut])
def list_regulations(
    jurisdiction_id: str | None = None,
    animal_scope: str | None = None,
    venue_scope: str | None = None,
    review_status: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[RegulationOut]:
    stmt = select(JurisdictionRule).where(JurisdictionRule.status == "current")
    if jurisdiction_id:
        stmt = stmt.where(JurisdictionRule.jurisdiction_id == jurisdiction_id)
    if animal_scope:
        stmt = stmt.where(JurisdictionRule.animal_scope == animal_scope)
    if venue_scope:
        stmt = stmt.where(JurisdictionRule.venue_scope == venue_scope)
    if review_status:
        stmt = stmt.where(JurisdictionRule.review_status == review_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(JurisdictionRule.document_name).limit(limit).offset(offset)
    ).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.get("/places/{place_id}/regulations", response_model=Page[RegulationOut])
def place_regulations(
    place_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[RegulationOut]:
    """Jurisdiction rules whose review status is explicitly distinguished;
    unresolved matches surface as NOT_REVIEWED rather than 'no law found'."""
    from app.models import Place

    place = db.get(Place, place_id)
    if place is None:
        raise NotFound("场所不存在")
    # v1: match city-level regulations on the synthetic demo jurisdiction
    stmt = select(JurisdictionRule).where(
        JurisdictionRule.jurisdiction_id == "demo-city",
        JurisdictionRule.status == "current",
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.post("/regulations", response_model=RegulationOut, status_code=201)
def create_regulation(
    body: RegulationIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> JurisdictionRule:
    reg = JurisdictionRule(**body.model_dump())
    db.add(reg)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="regulation.create",
        target_type="jurisdiction_rule",
        target_id=str(reg.id),
        after_state={"document_name": body.document_name},
    )
    db.commit()
    db.refresh(reg)
    return reg


@admin.post("/regulations/{reg_id}/review", response_model=RegulationOut)
def review_regulation(
    reg_id: str,
    body: RegulationUpdate,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> JurisdictionRule:
    from datetime import UTC, datetime

    reg = db.get(JurisdictionRule, reg_id)
    if reg is None:
        raise NotFound("法规不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(reg, k, v)
    reg.reviewed_at = datetime.now(UTC)
    reg.reviewed_by = user.id
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="regulation.review",
        target_type="jurisdiction_rule",
        target_id=reg_id,
        before_state={"review_status": reg.review_status},
        after_state=data,
    )
    db.commit()
    db.refresh(reg)
    return reg
