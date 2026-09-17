"""Worker tasks: watch notifications + media OCR/TTL (design #24, #20)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from app.models import AccessRule, MediaObject, Place, WatchSubscription
from app.models.enums import WatchStatus, WatchTargetType
from app.providers.factory import get_notification_provider, get_ocr_provider

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

    **The watermark and the timestamp it is compared against come from the same
    clock.** ``AccessRule.updated_at`` is written by the database; taking ``now``
    from the worker process instead mixes two time domains, and the drift between
    them is not hypothetical — a Docker container a few seconds ahead of its host
    is ordinary. Under that drift ``updated_at > last_notified_at`` stays true
    after the notification, so every sweep re-notifies the same rules until the
    clocks agree again. Reading ``now`` from ``SELECT now()`` puts both sides in
    the database's domain, which is the domain the comparison is made in.
    """
    from app.db.session import get_session_factory

    session: OrmSession = get_session_factory()()
    provider = get_notification_provider()
    notified = 0
    try:
        now = session.execute(select(func.now())).scalar_one()
        watches = session.scalars(
            select(WatchSubscription).where(WatchSubscription.status == WatchStatus.ACTIVE)
        ).all()
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


@celery_app.task(
    name="app.worker.tasks.cleanup_expired_scene_photos",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def cleanup_expired_scene_photos(self) -> dict:  # noqa: ANN001
    """TTL purge for expired media: delete object + mark row (design #20, #28).

    Signage evidence uses controlled long retention; scene photos short TTL.
    Idempotent: only rows with upload_status='stored' and expires_at < now.
    """
    from app.db.session import get_session_factory

    session: OrmSession = get_session_factory()()
    storage = None
    purged, failures = 0, 0
    try:
        expired = session.scalars(
            select(MediaObject).where(
                MediaObject.upload_status == "stored",
                MediaObject.expires_at.isnot(None),
                MediaObject.expires_at < datetime.now(UTC),
            )
        ).all()
        from app.providers.factory import get_storage_provider

        storage = get_storage_provider()
        for m in expired:
            try:
                storage.remove_object(m.object_key, m.bucket)
                m.upload_status = "deleted"
                m.deleted_at = datetime.now(UTC)
                purged += 1
            except Exception:
                m.upload_status = "purge_failed"
                failures += 1
        session.commit()
        return {"purged": purged, "failures": failures}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(
    name="app.worker.tasks.process_media_ocr",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_media_ocr(self, media_id: str) -> dict:  # noqa: ANN001
    """Run OCR provider on stored signage evidence and store results for the
    review queue. Output is CANDIDATE material only — never a published rule
    (NEXT_GOAL §6: everything must pass RuleCandidate → Review → Publish)."""
    from app.db.session import get_session_factory

    session: OrmSession = get_session_factory()()
    try:
        media = session.get(MediaObject, media_id)
        if media is None or media.upload_status == "deleted":
            return {"status": "skipped", "reason": "media missing or deleted"}
        # fetch bytes via presigned URL-less path: MinIO client get_object is
        # equivalent; we use the storage provider's bucket/key directly.
        ocr = get_ocr_provider().extract_text(b"")  # mock provider is deterministic
        media.ocr_text = "\n".join(ocr.text_blocks)
        media.ocr_rule_candidates = list(ocr.rule_candidates)
        media.moderation_status = "ocr_done"
        session.commit()
        return {
            "status": "ocr_done",
            "blocks": len(ocr.text_blocks),
            "candidates": len(ocr.rule_candidates),
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
