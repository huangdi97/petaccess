"""Verification endpoints — on-site quick confirm / changed / uncertain (design #15, #31)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFound
from app.core.idempotency import check_inflight, get_cached, store
from app.core.ratelimit import check_rate_limit
from app.core.security import get_current_user, get_optional_user, require_role
from app.db.session import get_db
from app.models import AccessRule, Place, User, VerificationEvent
from app.models.enums import UserRole, VerificationEventType
from app.schemas.civic import VerificationIn, VerificationOut
from app.schemas.common import Page

router = APIRouter(tags=["verifications"])


@router.get("/places/{place_id}/verifications", response_model=Page[VerificationOut])
def list_place_verifications(
    place_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[VerificationOut]:
    stmt = (
        select(VerificationEvent)
        .where(
            VerificationEvent.place_id == place_id,
            VerificationEvent.event_type.notin_(
                (
                    VerificationEventType.PLACE_CORRECTION,
                    VerificationEventType.RULE_LEAD_SUBMITTED,
                    VerificationEventType.SIGNAGE_UPLOADED,
                )
            ),
        )
        .order_by(VerificationEvent.occurred_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


def list_place_corrections(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[VerificationOut]:
    """Moderator-only queue for user-submitted place correction leads."""

    stmt = (
        select(VerificationEvent)
        .where(VerificationEvent.event_type == VerificationEventType.PLACE_CORRECTION)
        .order_by(VerificationEvent.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


# Explicit endpoint registration is intentional: it makes the route handler a
# real first-party reference for the dead-code gate instead of relying on
# decorator side effects that the static scanner cannot see.
router.add_api_route(
    "/admin/place-corrections",
    list_place_corrections,
    methods=["GET"],
    response_model=Page[VerificationOut],
)


def list_rule_leads(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[VerificationOut]:
    """Moderator-only queue for rule leads and signage evidence.

    These are pre-normative review inputs. They never appear in the public
    verification feed and never become AccessRule rows without the governed
    RuleCandidate -> Human Review -> Publish path.
    """

    stmt = (
        select(VerificationEvent)
        .where(
            VerificationEvent.event_type.in_(
                (
                    VerificationEventType.RULE_LEAD_SUBMITTED,
                    VerificationEventType.SIGNAGE_UPLOADED,
                )
            )
        )
        .order_by(VerificationEvent.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


router.add_api_route(
    "/admin/rule-leads",
    list_rule_leads,
    methods=["GET"],
    response_model=Page[VerificationOut],
)


@router.post("/verifications", response_model=VerificationOut, status_code=201)
def create_verification(
    body: VerificationIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationEvent:
    settings = get_settings()
    check_rate_limit(
        "verifications",
        user.id,
        settings.contribution_rate_max,
        settings.contribution_rate_window_seconds,
    )
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    if body.rule_id and db.get(AccessRule, body.rule_id) is None:
        raise NotFound("规则不存在")
    idem_key = request.headers.get("Idempotency-Key", "")
    if idem_key:
        cached = get_cached("verification", idem_key)
        if cached is not None:
            ev = db.get(VerificationEvent, cached["id"])
            if ev is not None:
                return ev
        check_inflight("verification", idem_key)
    ev = VerificationEvent(
        **body.model_dump(),
        user_id=user.id,
        occurred_at=datetime.now(UTC),
    )
    db.add(ev)
    # touching a rule refreshes its last-verified time (still_valid only)
    if body.rule_id and body.result == "still_valid":
        rule = db.get(AccessRule, body.rule_id)
        if rule:
            rule.last_verified_at = datetime.now(UTC)
    db.commit()
    db.refresh(ev)
    if idem_key:
        store("verification", idem_key, {"id": ev.id})
    return ev
