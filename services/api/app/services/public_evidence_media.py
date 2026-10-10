"""Fail-closed public evidence-media qualification.

Consumer media is deliberately narrower than public Reality facts:
- the artifact explicitly permits display;
- media review is approved;
- a human-verified published Reality fact cites the bundle;
- the object still exists and has not expired.

Private upload/owner routes remain in api.v1.media.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import (
    AnimalFacility,
    EvidenceBundle,
    MediaObject,
    ObservedPresence,
    SourceArtifact,
    StaffResponseObservation,
)
from app.models.enums import RealityVerificationStatus
from app.models.media import MediaModerationStatus, MediaUploadStatus
from app.providers.factory import get_storage_provider

PUBLIC_REALITY_VERIFICATION = {
    RealityVerificationStatus.HUMAN_VERIFIED.value,
    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
}
PUBLIC_MEDIA_URL_SECONDS = 300
PUBLIC_IMAGE_MIME = frozenset({"image/png", "image/jpeg", "image/webp"})


def _bundle_backs_published_reality(db: Session, bundle_id: str) -> bool:
    """Return true only for human-reviewed public Reality facts."""

    for model in (ObservedPresence, StaffResponseObservation, AnimalFacility):
        published_id = db.scalar(
            select(model.id)
            .where(
                model.evidence_bundle_id == bundle_id,
                model.verification_status.in_(PUBLIC_REALITY_VERIFICATION),
            )
            .limit(1)
        )
        if published_id is not None:
            return True
    return False


def resolve_public_evidence_media(db: Session, bundle_id: str) -> tuple[MediaObject, str]:
    """Resolve one display-safe object without revealing private-media existence."""

    unavailable = NotFound("公开证据媒体不可用")
    if not _bundle_backs_published_reality(db, bundle_id):
        raise unavailable

    bundle = db.get(EvidenceBundle, bundle_id)
    if bundle is None:
        raise unavailable
    artifact = db.get(SourceArtifact, bundle.artifact_id)
    if artifact is None or not artifact.display_allowed or not artifact.media_id:
        raise unavailable

    media = db.get(MediaObject, artifact.media_id)
    now = datetime.now(UTC)
    if (
        media is None
        or media.upload_status != MediaUploadStatus.STORED.value
        or media.deleted_at is not None
        or media.moderation_status != MediaModerationStatus.APPROVED.value
        or media.mime_type not in PUBLIC_IMAGE_MIME
        or (media.expires_at is not None and media.expires_at <= now)
    ):
        raise unavailable

    storage = get_storage_provider()
    if storage.stat_object(media.object_key, media.bucket) is None:
        raise unavailable
    url = storage.presigned_get_url(
        media.object_key,
        media.bucket,
        expires_seconds=PUBLIC_MEDIA_URL_SECONDS,
    )
    return media, url
