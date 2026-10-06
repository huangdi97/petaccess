"""Watch subscription endpoints (design #24, GOAL #16)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError, NotFound
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User, WatchSubscription
from app.models.enums import WatchDomain, WatchStatus, WatchTargetType
from app.schemas.civic import WatchIn, WatchOut

router = APIRouter(tags=["watches"])


@router.get("/watches", response_model=list[WatchOut])
def my_watches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return current subscriptions only; an unsubscribed row is history, not UI state."""
    return list(
        db.scalars(
            select(WatchSubscription).where(
                WatchSubscription.user_id == user.id,
                WatchSubscription.status != WatchStatus.UNSUBSCRIBED,
            )
        ).all()
    )


@router.post("/watches", response_model=WatchOut, status_code=201)
def subscribe(
    body: WatchIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WatchSubscription:
    if not get_settings().feature_watch:
        raise ApiError("关注功能未开放", code="feature_disabled", status_code=403)
    if body.watch_domain == WatchDomain.REALITY and body.target_type == WatchTargetType.RULE:
        raise ApiError(
            "现场更新只能关注场所或区域，不能把一条规范规则当作 Reality 目标",
            code="invalid_reality_watch_target",
            status_code=422,
        )
    existing = db.scalar(
        select(WatchSubscription).where(
            WatchSubscription.user_id == user.id,
            WatchSubscription.watch_domain == body.watch_domain,
            WatchSubscription.target_type == body.target_type,
            WatchSubscription.target_id == body.target_id,
        )
    )
    if existing:
        if existing.status == WatchStatus.UNSUBSCRIBED:
            existing.status = WatchStatus.ACTIVE
            db.commit()
            db.refresh(existing)
        return existing
    sub = WatchSubscription(
        user_id=user.id,
        watch_domain=body.watch_domain,
        target_type=body.target_type,
        target_id=body.target_id,
        channels=body.channels,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/watches/{watch_id}", status_code=204)
def unsubscribe(
    watch_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    sub = db.get(WatchSubscription, watch_id)
    if sub is None or sub.user_id != user.id:
        raise NotFound("关注不存在")
    sub.status = WatchStatus.UNSUBSCRIBED
    db.commit()
