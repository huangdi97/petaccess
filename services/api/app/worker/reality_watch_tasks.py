"""Reality Watch delivery — separate from normative Rule Watch."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from app.models import AnimalFacility, ObservedPresence, Place, StaffResponseObservation, WatchSubscription
from app.models.enums import RealityVerificationStatus, WatchDomain, WatchStatus, WatchTargetType
from app.providers.factory import get_notification_provider

from .celery_app import celery_app

VERIFIED_REALITY_STATUSES = (
    RealityVerificationStatus.HUMAN_VERIFIED.value,
    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
)


def _reality_changed_for_watch(
    session: OrmSession,
    watch: WatchSubscription,
    since: datetime,
) -> int:
    """Count newly published Reality facts after this subscription watermark."""

    def count_model(
        model: type[ObservedPresence] | type[StaffResponseObservation] | type[AnimalFacility],
    ) -> int:
        predicates = [
            model.verification_status.in_(VERIFIED_REALITY_STATUSES),
            func.coalesce(model.last_verified_at, model.created_at) > since,
        ]
        if watch.target_type == WatchTargetType.PLACE:
            predicates.append(model.place_id == watch.target_id)
        elif watch.target_type == WatchTargetType.ZONE:
            predicates.append(model.zone_id == watch.target_id)
        else:
            return 0
        return session.scalar(select(func.count()).select_from(model).where(*predicates)) or 0

    return sum(
        count_model(model)
        for model in (ObservedPresence, StaffResponseObservation, AnimalFacility)
    )


@celery_app.task(
    name="app.worker.reality_watch_tasks.notify_reality_changes",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def notify_reality_changes() -> dict:
    """Notify only on newly published, human-verified Reality facts."""

    from app.db.session import get_session_factory

    session: OrmSession = get_session_factory()()
    provider = get_notification_provider()
    notified = 0
    try:
        now = session.execute(select(func.now())).scalar_one()
        watches = session.scalars(
            select(WatchSubscription).where(
                WatchSubscription.status == WatchStatus.ACTIVE,
                WatchSubscription.watch_domain == WatchDomain.REALITY,
            )
        ).all()
        for watch in watches:
            since = watch.last_notified_at or datetime(2020, 1, 1, tzinfo=UTC)
            changed = _reality_changed_for_watch(session, watch, since)
            if not changed:
                continue
            place = (
                session.get(Place, watch.target_id)
                if watch.target_type == WatchTargetType.PLACE
                else None
            )
            title = f"现场更新：{place.canonical_name if place else watch.target_id}"
            body = f"该场所有 {changed} 条新的经核验现场事实。"
            provider.send(watch.user_id, (watch.channels or ["in_app"])[0], title, body)
            watch.last_notified_at = now
            notified += 1
        session.commit()
        return {"notified_watches": notified}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
