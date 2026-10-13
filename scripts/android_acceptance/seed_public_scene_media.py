#!/usr/bin/env python3
"""Seed one governed public scene photo for Android packaged-runtime acceptance.

The media-upload API itself is covered by integration tests. This runtime seed
focuses on the downstream contract that only a reviewed, display-allowed,
human-verified scene photo can reach the Consumer through the PetAccess API
origin and render inside the packaged Tauri WebView.

The script refuses production and unknown databases.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import uuid
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
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl8WQAAAABJRU5ErkJggg=="
)
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
            original_filename="android-runtime-scene.png",
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
                **evidence,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
