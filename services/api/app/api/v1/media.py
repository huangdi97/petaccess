"""Private media upload and controlled serving.

Every object is private. owner_type / owner_id describe the subject a file
belongs to; created_by_user_id describes who may read/delete it. Reviewers may
inspect evidence for moderation. Consumer endpoints never return a public
object-store URL.
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.config import get_settings
from app.core.errors import ApiError, NotFound
from app.core.media_sanitize import strip_image_metadata
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import MediaObject, User
from app.models.enums import UserRole
from app.models.media import MediaPrivacyClass, MediaPurpose
from app.providers.factory import get_storage_provider

router = APIRouter(tags=["media"])

ALLOWED_MIME = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/webp": b"RIFF",
}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MIME_EXTENSIONS = {
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/webp": {".webp"},
}
MAX_BYTES = 10 * 1024 * 1024

PRIVACY_BY_PURPOSE = {
    MediaPurpose.SIGNAGE_EVIDENCE: MediaPrivacyClass.EVIDENCE,
    MediaPurpose.IMPORT_DOCUMENT: MediaPrivacyClass.EVIDENCE,
    MediaPurpose.SCENE_PHOTO: MediaPrivacyClass.SCENE,
    MediaPurpose.AVATAR: MediaPrivacyClass.SCENE,
}


def _verify_magic(data: bytes, declared_mime: str) -> bool:
    magic = ALLOWED_MIME.get(declared_mime)
    return bool(magic and data.startswith(magic))


def _ttl_for(privacy_class: str) -> timedelta:
    settings = get_settings()
    if privacy_class == MediaPrivacyClass.EVIDENCE:
        return timedelta(days=settings.signage_retention_days)
    return timedelta(hours=settings.scene_photo_ttl_hours)


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


async def _validated_image(file: UploadFile) -> tuple[bytes, str, str, bool]:
    declared = file.content_type or ""
    if declared not in ALLOWED_MIME:
        raise ApiError("仅允许 PNG/JPEG/WebP 图片", code="unsupported_media_type", status_code=415)

    data = await file.read()
    if not data:
        raise ApiError("空文件", code="empty_file")
    if len(data) > MAX_BYTES:
        raise ApiError("文件超过 10MB 限制", code="payload_too_large", status_code=413)
    if not _verify_magic(data, declared):
        raise ApiError("文件内容与声明类型不符", code="magic_mismatch", status_code=415)

    filename = file.filename or ""
    ext = _extension(filename)
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ApiError("扩展名不在允许范围", code="invalid_extension", status_code=415)
    if ext and ext not in MIME_EXTENSIONS[declared]:
        raise ApiError("扩展名与 MIME 不一致", code="extension_mime_mismatch", status_code=415)

    sanitized, metadata_stripped = strip_image_metadata(data)
    return sanitized, declared, filename, metadata_stripped


def _reviewer(user: User) -> bool:
    return str(user.role) in {UserRole.MODERATOR.value, UserRole.ADMIN.value}


def _private_media(db: Session, media_id: str, user: User) -> MediaObject:
    media = db.get(MediaObject, media_id)
    if media is None or media.upload_status == "deleted":
        raise NotFound("媒体不存在")
    if media.created_by_user_id != user.id and not _reviewer(user):
        raise NotFound("媒体不存在")
    return media


def _create_media(
    db: Session,
    *,
    user: User,
    data: bytes,
    declared_mime: str,
    filename: str,
    purpose: str,
    owner_type: str | None,
    owner_id: str | None,
) -> tuple[MediaObject, str | None]:
    digest = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(
        select(MediaObject).where(
            MediaObject.created_by_user_id == user.id,
            MediaObject.sha256 == digest,
            MediaObject.upload_status == "stored",
            MediaObject.deleted_at.is_(None),
        )
    )
    duplicate_of = duplicate.id if duplicate else None

    object_key = f"media/{user.id[:8]}/{uuid.uuid4().hex}/{(filename or 'image')[-40:]}"
    privacy_class = PRIVACY_BY_PURPOSE[purpose]
    stored = get_storage_provider().put_object(object_key, data, declared_mime)
    media = MediaObject(
        owner_type=owner_type,
        owner_id=owner_id,
        created_by_user_id=user.id,
        purpose=purpose,
        privacy_class=privacy_class,
        bucket=stored["bucket"],
        object_key=object_key,
        mime_type=declared_mime,
        byte_size=len(data),
        sha256=digest,
        original_filename=filename[:255] or None,
        moderation_status="pending",
        expires_at=datetime.now(UTC) + _ttl_for(privacy_class),
    )
    db.add(media)
    db.flush()
    return media, duplicate_of


def _upload_response(media: MediaObject, duplicate_of: str | None) -> dict:
    return {
        "id": media.id,
        "purpose": media.purpose,
        "privacy_class": media.privacy_class,
        "byte_size": media.byte_size,
        "sha256": media.sha256,
        "duplicate_of": duplicate_of,
        "moderation_status": media.moderation_status,
        "expires_at": media.expires_at,
    }


@router.post("/media/upload", status_code=201)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    purpose: str = MediaPurpose.SIGNAGE_EVIDENCE,
    owner_type: str | None = None,
    owner_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if purpose not in MediaPurpose.ALL:
        raise ApiError("不支持的媒体用途", code="invalid_purpose")

    data, declared, filename, metadata_stripped = await _validated_image(file)
    media, duplicate_of = _create_media(
        db,
        user=user,
        data=data,
        declared_mime=declared,
        filename=filename,
        purpose=purpose,
        owner_type=owner_type,
        owner_id=owner_id,
    )
    record_audit(
        db,
        request=request,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.MEDIA_UPLOAD.value,
        target_type="media_object",
        target_id=media.id,
        after_state={
            "purpose": purpose,
            "sha256": media.sha256[:16],
            "duplicate_of": duplicate_of,
            "byte_size": len(data),
            "metadata_stripped": metadata_stripped,
        },
    )
    db.commit()
    return _upload_response(media, duplicate_of)


@router.get("/media/{media_id}/url")
def media_url(
    media_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return a short-lived URL only to the uploader or a reviewer."""
    media = _private_media(db, media_id, user)
    url = get_storage_provider().presigned_get_url(media.object_key, media.bucket)
    return {"id": media.id, "url": url, "expires_in": 900}


@router.get("/media/{media_id}")
def media_meta(
    media_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    media = _private_media(db, media_id, user)
    return {
        "id": media.id,
        "purpose": media.purpose,
        "privacy_class": media.privacy_class,
        "mime_type": media.mime_type,
        "byte_size": media.byte_size,
        "moderation_status": media.moderation_status,
        "ocr_text": media.ocr_text,
        "ocr_rule_candidates": media.ocr_rule_candidates,
        "upload_status": media.upload_status,
        "created_at": media.created_at,
        "expires_at": media.expires_at,
        "deleted_at": media.deleted_at,
    }


@router.delete("/media/{media_id}", status_code=204)
def delete_media(
    media_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    media = _private_media(db, media_id, user)
    get_storage_provider().remove_object(media.object_key, media.bucket)
    media.upload_status = "deleted"
    media.deleted_at = datetime.now(UTC)
    record_audit(
        db,
        request=request,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.MEDIA_DELETE.value,
        target_type="media_object",
        target_id=media.id,
        before_state={"upload_status": "stored"},
        after_state={"upload_status": "deleted"},
    )
    db.commit()
