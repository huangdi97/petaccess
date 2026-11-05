"""Authenticated privacy-rights endpoints.

This is intentionally narrower than an administrative erasure engine:
- /privacy/export returns a structured copy of the caller's own account data;
- account deletion is an auditable, idempotent request, not instant physical
  deletion of provenance that may require de-identification/retention review.

No endpoint claims deletion has completed until a governed processor exists.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import AuditLog, MediaObject, PetProfile, User, WatchSubscription
from app.models.v05 import BoundaryProfile
from app.services.contribution_activity import contribution_activity

router = APIRouter(prefix="/privacy", tags=["privacy"])


def _value(value: object | None) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _deletion_request(db: Session, user_id: str) -> AuditLog | None:
    return db.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == user_id,
            AuditLog.action == AuditEvent.PRIVACY_ACCOUNT_DELETION_REQUEST.value,
            AuditLog.target_type == "user",
            AuditLog.target_id == user_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )


def _deletion_status(row: AuditLog | None) -> dict:
    if row is None:
        return {"status": "none", "requested_at": None}
    return {
        "status": str((row.after_state or {}).get("status") or "submitted"),
        "requested_at": row.created_at,
    }


@router.get("/account-deletion-request")
def account_deletion_request_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return _deletion_status(_deletion_request(db, user.id))


@router.post("/account-deletion-request", status_code=202)
def request_account_deletion(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    existing = _deletion_request(db, user.id)
    if existing is not None:
        return _deletion_status(existing)

    record_audit(
        db,
        request=request,
        actor_user_id=user.id,
        actor_role=_value(user.role),
        action=AuditEvent.PRIVACY_ACCOUNT_DELETION_REQUEST.value,
        target_type="user",
        target_id=user.id,
        after_state={
            "status": "submitted",
            "processing_policy": "delete_or_deidentify_after_retention_review",
        },
        detail={
            "consumer_requested": True,
            "instant_physical_deletion": False,
        },
    )
    db.commit()
    return _deletion_status(_deletion_request(db, user.id))


@router.get("/export")
def export_my_data(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    pets = db.scalars(
        select(PetProfile).where(PetProfile.user_id == user.id).order_by(PetProfile.created_at)
    ).all()
    boundaries = db.scalars(
        select(BoundaryProfile)
        .options(selectinload(BoundaryProfile.preferences))
        .where(BoundaryProfile.user_id == user.id)
        .order_by(BoundaryProfile.created_at)
    ).all()
    watches = db.scalars(
        select(WatchSubscription)
        .where(WatchSubscription.user_id == user.id)
        .order_by(WatchSubscription.created_at)
    ).all()
    media = db.scalars(
        select(MediaObject)
        .where(MediaObject.created_by_user_id == user.id)
        .order_by(MediaObject.created_at)
    ).all()

    payload = {
        "exported_at": datetime.now(UTC),
        "account": {
            "id": user.id,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "role": _value(user.role),
            "status": _value(user.status),
            "created_at": user.created_at,
        },
        "pets": [
            {
                "id": pet.id,
                "display_name": pet.display_name,
                "species": _value(pet.species),
                "breed_text": pet.breed_text,
                "weight_kg": float(pet.weight_kg) if pet.weight_kg is not None else None,
                "shoulder_height_cm": (
                    float(pet.shoulder_height_cm) if pet.shoulder_height_cm is not None else None
                ),
                "service_role": _value(pet.service_role),
                "registration_status": pet.registration_status,
                "vaccination_status": pet.vaccination_status,
                "birth_date": pet.birth_date,
                "created_at": pet.created_at,
            }
            for pet in pets
        ],
        "boundary_profiles": [
            {
                "id": profile.id,
                "name": profile.name,
                "is_default": profile.is_default,
                "created_at": profile.created_at,
                "preferences": [
                    {
                        "attribute": pref.attribute,
                        "stance": pref.stance,
                        "note": pref.note,
                    }
                    for pref in profile.preferences
                ],
            }
            for profile in boundaries
        ],
        "watches": [
            {
                "id": watch.id,
                "watch_domain": _value(watch.watch_domain),
                "target_type": _value(watch.target_type),
                "target_id": watch.target_id,
                "channels": watch.channels,
                "status": _value(watch.status),
                "created_at": watch.created_at,
            }
            for watch in watches
        ],
        "contribution_activity": contribution_activity(db, user.id),
        "uploaded_media": [
            {
                "id": item.id,
                "purpose": item.purpose,
                "privacy_class": item.privacy_class,
                "original_filename": item.original_filename,
                "byte_size": int(item.byte_size),
                "moderation_status": item.moderation_status,
                "upload_status": item.upload_status,
                "expires_at": item.expires_at,
                "created_at": item.created_at,
            }
            for item in media
        ],
        "account_deletion_request": _deletion_status(_deletion_request(db, user.id)),
        "retention_note": (
            "已发布贡献与证据可能因可追溯/审计要求在去标识化后保留；"
            "本导出不包含密码哈希、对象存储内部路径或其他用户数据。"
        ),
    }

    record_audit(
        db,
        request=request,
        actor_user_id=user.id,
        actor_role=_value(user.role),
        action=AuditEvent.PRIVACY_EXPORT.value,
        target_type="user",
        target_id=user.id,
        after_state={"sections": sorted(payload.keys())},
    )
    db.commit()
    return payload
