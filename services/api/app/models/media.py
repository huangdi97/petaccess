"""MediaObject: object-storage metadata with privacy classes and TTL
(NEXT_GOAL Track A1, design #20).

Raw objects live in MinIO under randomized keys; this row is the only index.
Evidence never gets public URLs — presigned GET only (PROVIDER_HARDENING_SPEC).
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, TimestampMixin


class MediaPurpose:
    SIGNAGE_EVIDENCE = "signage_evidence"
    SCENE_PHOTO = "scene_photo"
    AVATAR = "avatar"
    IMPORT_DOCUMENT = "import_document"

    ALL = [SIGNAGE_EVIDENCE, SCENE_PHOTO, AVATAR, IMPORT_DOCUMENT]


class MediaPrivacyClass:
    """signage evidence: controlled long retention; scene photos: short TTL (design #20)."""

    EVIDENCE = "evidence"
    SCENE = "scene"

    ALL = [EVIDENCE, SCENE]


class MediaObject(Base, PkMixin, TimestampMixin):
    __tablename__ = "media_object"
    __table_args__ = (
        Index("ix_media_object_owner", "owner_type", "owner_id"),
        Index("ix_media_object_expires", "expires_at"),
        Index("uq_media_object_key", "object_key", unique=True),
    )

    owner_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    privacy_class: Mapped[str] = mapped_column(String(20), nullable=False)

    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_key: Mapped[str] = mapped_column(String(240), nullable=False)

    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    byte_size: Mapped[int] = mapped_column(Numeric(14), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    upload_status: Mapped[str] = mapped_column(
        String(20), default="stored", nullable=False
    )  # stored | deleted | purge_failed
    moderation_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending | ocr_done | approved | rejected

    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )

    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_rule_candidates: Mapped[list | None] = mapped_column(JSON, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
