"""Uploader/reviewer-scoped media access and consumer-safe metadata projection."""

from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import MediaObject, User
from app.models.enums import UserRole
from app.models.media import MediaUploadStatus


def reviewer(user: User) -> bool:
    return str(user.role) in {UserRole.MODERATOR.value, UserRole.ADMIN.value}


def private_media(db: Session, media_id: str, user: User) -> MediaObject:
    media = db.get(MediaObject, media_id)
    if media is None or media.upload_status == MediaUploadStatus.DELETED.value:
        raise NotFound("媒体不存在")
    if media.created_by_user_id != user.id and not reviewer(user):
        # Deliberately indistinguishable from absence: do not disclose another
        # uploader's media identifier or retention state.
        raise NotFound("媒体不存在")
    return media


def media_meta_response(media: MediaObject) -> dict:
    """Public API metadata never includes bucket/object_key/storage URLs."""
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
