"""Source (provenance) endpoints (design #13, #31)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.security import get_optional_user, require_role
from app.db.session import get_db
from app.models import Source, User
from app.models.enums import UserRole
from app.schemas.civic import SourceIn, SourceOut
from app.schemas.common import Page

router = APIRouter(tags=["sources"])
admin = APIRouter(tags=["admin:sources"])


@router.get("/sources", response_model=Page[SourceOut])
def list_sources(
    source_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[SourceOut]:
    stmt = select(Source)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Source.collected_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.post("/sources", response_model=SourceOut, status_code=201)
def create_source(
    body: SourceIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Source:
    source = Source(
        source_type=body.source_type,
        issuer=body.issuer,
        issuer_verification=body.issuer_verification,
        source_url=body.source_url,
        collected_at=datetime.now(UTC),
        observed_at=body.observed_at,
        published_at=body.published_at,
        directness=body.directness,
        spatial_precision=body.spatial_precision,
        notes=body.notes,
    )
    db.add(source)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="source.create",
        target_type="source",
        target_id=str(source.id),
        after_state={"source_type": body.source_type.value, "issuer": body.issuer},
    )
    db.commit()
    db.refresh(source)
    return source
