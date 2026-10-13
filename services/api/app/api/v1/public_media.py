"""Governed public media delivery for Consumer surfaces.

Public media is stricter than public Reality data: every request re-checks that
the artifact is display-allowed, moderation-approved, unexpired, present in
storage and attached to a human-verified published Reality fact.

The Consumer receives only a PetAccess API URL. Object-storage topology and
presigned URLs remain private implementation details.
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.db.session import get_db
from app.providers.factory import get_storage_provider
from app.services.public_evidence_media import (
    PUBLIC_MEDIA_URL_SECONDS,
    resolve_public_evidence_media_object,
)

router = APIRouter(tags=["media"])


@router.get("/evidence-bundles/{bundle_id}/public-media")
def public_evidence_media(
    bundle_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Return the governed API URL for explicitly display-approved evidence."""

    media = resolve_public_evidence_media_object(db, bundle_id)
    url = request.url_for("public_evidence_media_content", bundle_id=bundle_id)
    return {
        "evidence_bundle_id": bundle_id,
        "media_id": media.id,
        "purpose": media.purpose,
        "url": str(url),
        "mime_type": media.mime_type,
        # Compatibility field retained from the former presigned-URL contract.
        # Qualification is still re-evaluated on every content request.
        "expires_in": PUBLIC_MEDIA_URL_SECONDS,
    }


@router.get(
    "/evidence-bundles/{bundle_id}/public-media/content",
    name="public_evidence_media_content",
)
def public_evidence_media_content(
    bundle_id: str,
    db: Session = Depends(get_db),
) -> Response:
    """Serve one currently qualified public image through the PetAccess API."""

    media = resolve_public_evidence_media_object(db, bundle_id)
    try:
        data = get_storage_provider().read_object(media.object_key, media.bucket)
    except Exception as exc:
        raise NotFound("公开证据媒体不可用") from exc
    return Response(
        content=data,
        media_type=media.mime_type,
        headers={
            "Cache-Control": "private, max-age=60, no-transform",
            "X-Content-Type-Options": "nosniff",
        },
    )
