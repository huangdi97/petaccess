"""Public API shapes for uploader-owned media metadata.

These schemas never expose object-store bucket/key or private presigned URLs.
"""

from datetime import datetime

from pydantic import BaseModel


class MediaMetaOut(BaseModel):
    id: str
    purpose: str
    privacy_class: str
    mime_type: str
    byte_size: int
    moderation_status: str
    ocr_text: str | None = None
    ocr_rule_candidates: list[dict] | None = None
    upload_status: str
    created_at: datetime
    expires_at: datetime | None = None
    deleted_at: datetime | None = None
