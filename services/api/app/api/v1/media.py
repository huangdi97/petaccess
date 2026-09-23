"""Media upload/serving endpoints (NEXT_GOAL Track A1).

Security (NEXT_GOAL §9 / design #20):
- MIME allowlist + magic-byte verification (no trust in client headers)
- size limit
- randomized object keys (no path traversal)
- sha256 + duplicate detection
- presigned GET only; evidence never public
- audit on upload/delete
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
from app.core.errors import ApiError, NotFound, PermissionDenied
from app.core.media_sanitize import strip_image_metadata
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import MediaObject, User
from app.models.media import MediaPrivacyClass, MediaPurpose
from app.providers.factory import get_storage_provider

router = APIRouter(tags=["media"])

ALLOWED_MIME = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/webp": b"RIFF",
}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_BYTES = 10 * 1024 * 1024

PRIVACY_BY_PURPOSE = {
    MediaPurpose.SIGNAGE_EVIDENCE: MediaPrivacyClass.EVIDENCE,
    MediaPurpose.IMPORT_DOCUMENT: MediaPrivacyClass.EVIDENCE,
    MediaPurpose.SCENE_PHOTO: MediaPrivacyClass.SCENE,
    MediaPurpose.AVATAR: MediaPrivacyClass.SCENE,
}


def _verify_magic(data: bytes, declared_mime: str) -> bool:
    magic = ALLOWED_MIME.get(declared_mime)
    if magic is None:
        return False
    return data.startswith(magic)


def _ttl_for(privacy_class: str) -> timedelta:
    s = get_settings()
    if privacy_class == MediaPrivacyClass.EVIDENCE:
        return timedelta(days=s.signage_retention_days)
    return timedelta(hours=s.scene_photo_ttl_hours)


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
    declared = file.content_type or ""
    if declared not in ALLOWED_MIME:
        raise ApiError("仅允许 PNG/JPEG/WebP 图片", code="unsupported_media_type", status_code=415)
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise ApiError("文件超过 10MB 限制", code="payload_too_large", status_code=413)
    if not data:
        raise ApiError("空文件", code="empty_file")
    # magic-byte check: client content-type headers are not trusted
    if not _verify_magic(data, declared):
        raise ApiError("文件内容与声明类型不符", code="magic_mismatch", status_code=415)
    original_name = file.filename or ""
    ext = ("." + original_name.rsplit(".", 1)[-1].lower()) if "." in original_name else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ApiError("扩展名不在允许范围", code="invalid_extension", status_code=415)
    if ext and declared == "image/png" and ext not in (".png",):
        raise ApiError("扩展名与 MIME 不一致", code="extension_mime_mismatch", status_code=415)
    if ext and declared in ("image/jpeg",) and ext not in (".jpg", ".jpeg"):
        raise ApiError("扩展名与 MIME 不一致", code="extension_mime_mismatch", status_code=415)
    if ext and declared == "image/webp" and ext != ".webp":
        raise ApiError("扩展名与 MIME 不一致", code="extension_mime_mismatch", status_code=415)

    # Privacy (SECURITY_FINAL_REPORT Phase 26): strip embedded EXIF/XMP/PNG-text
    # metadata BEFORE the blob reaches storage, so GPS / camera / timestamp
    # metadata never lands in the object store. The sanitizer is conservative:
    # an unparsable image is stored unchanged (``stripped=False``), never
    # corrupted; the sha256 below is computed on the stored bytes.
    data, meta_stripped = strip_image_metadata(data)
    sha256 = hashlib.sha256(data).hexdigest()

    # duplicate basic check: identical hash from same user, still stored
    dup = db.scalar(
        select(MediaObject).where(
            MediaObject.sha256 == sha256,
            MediaObject.upload_status == "stored",
            MediaObject.deleted_at.is_(None),
        )
    )
    duplicate_of = dup.id if dup else None

    # randomized key: no user-controlled path component
    object_key = f"media/{user.id[:8]}/{uuid.uuid4().hex}/{(original_name or 'image')[-40:]}"
    privacy_class = PRIVACY_BY_PURPOSE[purpose]
    storage = get_storage_provider()
    stored = storage.put_object(object_key, data, declared)

    media = MediaObject(
        owner_type=owner_type,
        owner_id=owner_id,
        purpose=purpose,
        privacy_class=privacy_class,
        bucket=stored["bucket"],
        object_key=object_key,
        mime_type=declared,
        byte_size=len(data),
        sha256=sha256,
        original_filename=original_name[:255] or None,
        moderation_status="pending",
        expires_at=datetime.now(UTC) + _ttl_for(privacy_class),
    )
    db.add(media)
    db.flush()
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
            "sha256": sha256[:16],
            "duplicate_of": duplicate_of,
            "byte_size": len(data),
        },
    )
    db.commit()
    return {
        "id": media.id,
        "purpose": purpose,
        "privacy_class": privacy_class,
        "byte_size": len(data),
        "sha256": sha256,
        "duplicate_of": duplicate_of,
        "moderation_status": media.moderation_status,
        "expires_at": media.expires_at,
    }


@router.get("/media/{media_id}/url")
def media_url(
    media_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Presigned GET (15 min). Evidence media is never publicly readable."""
    media = db.get(MediaObject, media_id)
    if media is None or media.upload_status == "deleted":
        raise NotFound("媒体不存在")
    url = get_storage_provider().presigned_get_url(media.object_key, media.bucket)
    return {"id": media.id, "url": url, "expires_in": 900}


@router.get("/media/{media_id}")
def media_meta(
    media_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    media = db.get(MediaObject, media_id)
    if media is None:
        raise NotFound("媒体不存在")
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
    media = db.get(MediaObject, media_id)
    if media is None or media.upload_status == "deleted":
        raise NotFound("媒体不存在")
    if media.owner_id and media.owner_id != user.id and user.role not in ("moderator", "admin"):
        raise PermissionDenied("无权删除该媒体")
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
