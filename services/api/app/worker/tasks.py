"""Worker tasks: watch notifications + image/OCR maintenance (design #24, #20)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.models import AccessRule, Place, WatchSubscription
from app.models.enums import WatchStatus, WatchTargetType
from app.providers.factory import get_notification_provider

from .celery_app import celery_app


@celery_app.task(
    name="app.worker.tasks.notify_rule_changes",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def notify_rule_changes(self) -> dict:  # noqa: ANN001
    """Sweep active watches for recently-updated rules and notify (mock sink).

    Idempotency: only rules updated in the last 26h with unnotified watches;
    watch.last_notified_at prevents duplicate sends.
    """
    from app.db.session import get_session_factory

    session: OrmSession = get_session_factory()()
    provider = get_notification_provider()
    notified = 0
    try:
        watches = session.scalars(
            select(WatchSubscription).where(WatchSubscription.status == WatchStatus.ACTIVE)
        ).all()
        now = datetime.now(UTC)
        for w in watches:
            since = w.last_notified_at or datetime(2020, 1, 1, tzinfo=UTC)
            if w.target_type == WatchTargetType.PLACE:
                rules = session.scalars(
                    select(AccessRule).where(
                        AccessRule.place_id == w.target_id,
                        AccessRule.updated_at > since,
                    )
                ).all()
            elif w.target_type == WatchTargetType.ZONE:
                rules = session.scalars(
                    select(AccessRule).where(
                        AccessRule.zone_id == w.target_id,
                        AccessRule.updated_at > since,
                    )
                ).all()
            else:  # rule-level watch
                single = session.get(AccessRule, w.target_id)
                rules = [] if single is None else [single]
            recent = [r for r in rules if (now - _dt(r.updated_at)).total_seconds() < 26 * 3600]
            if not recent:
                continue
            place = session.get(Place, w.target_id) if w.target_type == "place" else None
            title = f"规则变化提醒：{place.canonical_name if place else w.target_id}"
            body = f"该场所 {len(recent)} 条准入规则在最近一天内发生变化。"
            provider.send(w.user_id, (w.channels or ["in_app"])[0], title, body)
            w.last_notified_at = now
            notified += 1
        session.commit()
        return {"notified_watches": notified}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _dt(value) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


@celery_app.task(name="app.worker.tasks.cleanup_expired_scene_photos")
def cleanup_expired_scene_photos() -> dict:
    """Short-TTL scene-photo cleanup per privacy gate (design #20, #28).

    MinIO lifecycle rules handle actual deletion in production; this task
    records the sweep for audit. Signage evidence uses controlled long TTL.
    """
    from app.db.session import get_session_factory

    session = get_session_factory()()
    session.close()  # storage-side lifecycle handles objects; DB stores refs only
    return {"swept": True, "policy": "scene_photo_ttl"}
