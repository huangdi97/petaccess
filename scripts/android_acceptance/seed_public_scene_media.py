#!/usr/bin/env python3
"""Seed one governed public scene photo for Android packaged-runtime acceptance.

The media-upload API itself is covered by integration tests. This runtime seed
focuses on the downstream contract that only a reviewed, display-allowed,
human-verified scene photo can reach the Consumer through the PetAccess API
origin and render inside the packaged Tauri WebView.

The script refuses production and unknown databases.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import uuid
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.db.safety import DatabaseRole, classify_database_name, probe_database_name  # noqa: E402
from app.db.session import get_engine, get_session_factory  # noqa: E402
from app.models import (  # noqa: E402
    EvidenceBundle,
    MediaObject,
    ObservedPresence,
    RealityCandidate,
    SourceArtifact,
)
from app.providers.factory import get_storage_provider  # noqa: E402

PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e"
API_BASE = os.environ.get("PETACCESS_PREVIEW_API_BASE", "http://127.0.0.1:8000/api/v1").rstrip("/")
FIXTURE_WIDTH = 640
FIXTURE_HEIGHT = 480


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _runtime_scene_fixture_png() -> bytes:
    """Return a visible, deterministic CI fixture — never a fake venue photo.

    The old acceptance seed used a 1x1 image. It proved byte delivery but
    produced a giant blank 4:3 panel in packaged-runtime review boards, which
    looked like a product rendering defect. This raster is deliberately
    non-photographic: a green test-card composition with oversized "CI" marks.
    It exists only in isolated TEST/E2E/VISUAL databases.
    """

    width = FIXTURE_WIDTH
    height = FIXTURE_HEIGHT
    bg = (239, 245, 240)
    panel = (249, 251, 248)
    line = (72, 111, 91)
    accent = (190, 218, 202)
    muted = (221, 233, 226)

    def pixel(x: int, y: int) -> tuple[int, int, int]:
        # framed card
        if x < 28 or x >= width - 28 or y < 28 or y >= height - 28:
            return bg
        if x < 34 or x >= width - 34 or y < 34 or y >= height - 34:
            return line

        # abstract blocks: intentionally diagrammatic, never photo-like
        if 72 <= x < 236 and 168 <= y < 340:
            return accent
        if 278 <= x < 560 and 118 <= y < 340:
            return muted

        # giant block-letter C
        if 88 <= x < 166 and 70 <= y < 82:
            return line
        if 88 <= x < 100 and 70 <= y < 132:
            return line
        if 88 <= x < 166 and 120 <= y < 132:
            return line

        # giant block-letter I
        if 184 <= x < 248 and 70 <= y < 82:
            return line
        if 210 <= x < 222 and 70 <= y < 132:
            return line
        if 184 <= x < 248 and 120 <= y < 132:
            return line

        # lower baseline + corner markers make fixture identity obvious
        if 60 <= x < 580 and 382 <= y < 386:
            return line
        if (60 <= x < 74 and 398 <= y < 412) or (566 <= x < 580 and 398 <= y < 412):
            return line

        return panel

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # PNG filter: None
        for x in range(width):
            raw.extend(pixel(x, y))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    text = b"Description\x00CI FIXTURE - NOT A REAL PLACE PHOTO"
    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", text)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


PNG = _runtime_scene_fixture_png()
ALLOWED_ROLES = {DatabaseRole.TEST, DatabaseRole.E2E, DatabaseRole.VISUAL}


def _assert_isolated_database() -> str:
    name = probe_database_name(get_engine())
    role = classify_database_name(name)
    if role not in ALLOWED_ROLES:
        raise RuntimeError(
            f"refusing Android scene-media fixture on database={name!r} role={role.value}"
        )
    return name


def _seed_scene() -> tuple[str, str]:
    now = datetime.now(UTC)
    digest = hashlib.sha256(PNG).hexdigest()
    object_key = f"runtime/android-preview/{uuid.uuid4().hex}/scene.png"
    storage = get_storage_provider()
    stored = storage.put_object(object_key, PNG, "image/png")

    with get_session_factory()() as db:
        media = MediaObject(
            owner_type="place",
            owner_id=PLACE_ID,
            created_by_user_id=None,
            purpose="scene_photo",
            privacy_class="scene",
            bucket=stored["bucket"],
            object_key=object_key,
            mime_type="image/png",
            byte_size=len(PNG),
            sha256=digest,
            original_filename="android-runtime-ci-scene-fixture.png",
            upload_status="stored",
            moderation_status="approved",
            expires_at=now + timedelta(days=1),
        )
        db.add(media)
        db.flush()

        artifact = SourceArtifact(
            source_platform="platform_upload",
            collector_type="OnsiteEvidenceCollector",
            artifact_type="uploaded_image",
            media_id=media.id,
            content_hash=digest,
            collected_at=now,
            publisher_type="ordinary_user",
            display_allowed=True,
            redistribution_allowed=False,
        )
        db.add(artifact)
        db.flush()

        bundle = EvidenceBundle(
            artifact_id=artifact.id,
            source_platform="platform_upload",
            publisher_type="ordinary_user",
            captured_at=now,
            evidence_class="original",
            content_hash=digest,
        )
        db.add(bundle)
        db.flush()

        candidate = RealityCandidate(
            candidate_type="observed_presence",
            place_id=PLACE_ID,
            evidence_bundle_id=bundle.id,
            animal_scope="dog",
            observed_at=now,
            captured_at=now,
            review_status="APPROVED",
            reality_decision="VERIFIED",
            verification_status="human_verified",
            published_at=now,
        )
        db.add(candidate)
        db.flush()

        db.add(
            ObservedPresence(
                candidate_id=candidate.id,
                place_id=PLACE_ID,
                animal_scope="dog",
                observed_action="present",
                observed_at=now,
                captured_at=now,
                evidence_bundle_id=bundle.id,
                verification_status="human_verified",
                last_verified_at=now,
            )
        )
        db.commit()
        return str(media.id), str(bundle.id)


def _verify_delivery(media_id: str, bundle_id: str) -> dict[str, str]:
    with httpx.Client(timeout=20) as client:
        metadata = client.get(f"{API_BASE}/evidence-bundles/{bundle_id}/public-media")
        metadata.raise_for_status()
        body = metadata.json()
        if body.get("media_id") != media_id:
            raise RuntimeError("public-media metadata resolved the wrong media object")
        if body.get("purpose") != "scene_photo":
            raise RuntimeError(f"public-media purpose is not scene_photo: {body.get('purpose')!r}")

        url = str(body.get("url") or "")
        expected_suffix = f"/api/v1/evidence-bundles/{bundle_id}/public-media/content"
        if not url.endswith(expected_suffix):
            raise RuntimeError(f"public media did not resolve through API origin: {url}")
        if ":9000" in url or url.startswith("nullstorage://"):
            raise RuntimeError(f"object-storage origin leaked into Consumer URL: {url}")

        image = client.get(f"{API_BASE}/evidence-bundles/{bundle_id}/public-media/content")
        image.raise_for_status()
        if not image.headers.get("content-type", "").startswith("image/png"):
            raise RuntimeError(
                f"unexpected public scene MIME: {image.headers.get('content-type')!r}"
            )
        if image.content[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("public scene content is not a PNG")
        width, height = struct.unpack(">II", image.content[16:24])
        if (width, height) != (FIXTURE_WIDTH, FIXTURE_HEIGHT):
            raise RuntimeError(f"runtime scene fixture dimensions drifted: {(width, height)!r}")

        return {"media_id": media_id, "bundle_id": bundle_id, "url": url}


def main() -> int:
    database = _assert_isolated_database()
    media_id, bundle_id = _seed_scene()
    evidence = _verify_delivery(media_id, bundle_id)
    print(
        json.dumps(
            {
                "result": "PASS",
                "database": database,
                "place_id": PLACE_ID,
                "fixture": True,
                "fixture_kind": "ci_scene_media",
                "fixture_label": "CI FIXTURE - NOT A REAL PLACE PHOTO",
                "fixture_dimensions": [FIXTURE_WIDTH, FIXTURE_HEIGHT],
                **evidence,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
