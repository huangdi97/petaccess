"""Track A1 integration tests: real MinIO upload → metadata → OCR task →
delete/TTL → object removal → audit. Hits the dockerized MinIO (:9000)."""

import hashlib
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _png_bytes(seed: bytes = b"x") -> bytes:
    # minimal valid PNG header (magic bytes are what the API verifies)
    return b"\x89PNG\r\n\x1a\n" + seed + b"0" * 64


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def user_token(client):
    email = f"media-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "媒体测试", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _media_ids(client, tok):
    """Helper: run the TTL purge logic directly against the DB."""
    from datetime import UTC, datetime

    from app.db.session import get_session_factory
    from app.models import MediaObject
    from app.providers.factory import get_storage_provider

    s = get_session_factory()()
    rows = s.scalars(
        select(MediaObject).where(
            MediaObject.upload_status == "stored",
            MediaObject.expires_at < datetime.now(UTC),
        )
    ).all()
    storage = get_storage_provider()
    purged = []
    for m in rows:
        storage.remove_object(m.object_key, m.bucket)
        m.upload_status = "deleted"
        m.deleted_at = datetime.now(UTC)
        purged.append(m.id)
    s.commit()
    s.close()
    return purged


from sqlalchemy import select  # noqa: E402


def test_upload_minio_object_metadata_and_presigned(client, user_token):
    data = _png_bytes(b"sign1")
    r = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("rule-sign.png", data, "image/png")},
        headers=_auth(user_token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["privacy_class"] == "evidence"
    assert body["sha256"] == hashlib.sha256(data).hexdigest()

    # object really exists in MinIO with matching size
    from app.db.session import get_session_factory
    from app.models import MediaObject
    from app.providers.factory import get_storage_provider

    s = get_session_factory()()
    media = s.get(MediaObject, body["id"])
    assert media is not None
    st = get_storage_provider().stat_object(media.object_key, media.bucket)
    assert st is not None and st["size"] == len(data)

    # presigned URL works and is the only access path
    url_r = client.get(f"/api/v1/media/{media.id}/url", headers=_auth(user_token))
    assert url_r.status_code == 200
    assert url_r.json()["url"].startswith("http")

    # audit row exists (direct DB check: admin endpoint requires moderator role)
    from app.models import AuditLog

    a = s.scalars(
        select(AuditLog).where(AuditLog.action == "media.upload", AuditLog.target_id == media.id)
    ).all()
    assert len(a) == 1
    s.close()


def test_upload_rejects_bad_content(client, user_token):
    # text disguised as png → magic mismatch
    r1 = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("fake.png", b"this is not an image at all", "image/png")},
        headers=_auth(user_token),
    )
    assert r1.status_code == 415
    assert r1.json()["error"]["code"] == "magic_mismatch"

    # unsupported MIME
    r2 = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=_auth(user_token),
    )
    assert r2.status_code == 415

    # extension/MIME mismatch
    r3 = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("photo.jpg", _png_bytes(), "image/png")},
        headers=_auth(user_token),
    )
    assert r3.status_code == 415

    # oversize (>10MB)
    big = _png_bytes() + b"0" * (10 * 1024 * 1024)
    r4 = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("big.png", big, "image/png")},
        headers=_auth(user_token),
    )
    assert r4.status_code == 413


def test_ocr_task_updates_media_for_review_queue(client, user_token):
    r = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("sign2.png", _png_bytes(b"sign2"), "image/png")},
        headers=_auth(user_token),
    )
    media_id = r.json()["id"]

    from app.worker.tasks import process_media_ocr

    result = process_media_ocr.delay(media_id).get(timeout=30)
    assert result["status"] == "ocr_done"

    meta = client.get(f"/api/v1/media/{media_id}", headers=_auth(user_token)).json()
    assert meta["moderation_status"] == "ocr_done"
    assert meta["ocr_text"], "mock OCR should produce text blocks"
    assert isinstance(meta["ocr_rule_candidates"], list) and meta["ocr_rule_candidates"]


def test_delete_removes_minio_object(client, user_token):
    r = client.post(
        "/api/v1/media/upload",
        params={"purpose": "scene_photo"},
        files={"file": ("scene.png", _png_bytes(b"scene"), "image/png")},
        headers=_auth(user_token),
    )
    media_id = r.json()["id"]
    from app.db.session import get_session_factory
    from app.models import MediaObject
    from app.providers.factory import get_storage_provider

    s = get_session_factory()()
    media = s.get(MediaObject, media_id)
    key, bucket = media.object_key, media.bucket
    assert get_storage_provider().stat_object(key, bucket) is not None
    s.close()

    dr = client.delete(f"/api/v1/media/{media_id}", headers=_auth(user_token))
    assert dr.status_code == 204
    assert get_storage_provider().stat_object(key, bucket) is None


def test_ttl_purge_removes_expired(client, user_token):
    from datetime import UTC, datetime, timedelta

    from app.db.session import get_session_factory
    from app.models import MediaObject

    r = client.post(
        "/api/v1/media/upload",
        params={"purpose": "scene_photo"},
        files={"file": ("expired.png", _png_bytes(b"exp"), "image/png")},
        headers=_auth(user_token),
    )
    media_id = r.json()["id"]
    s = get_session_factory()()
    media = s.get(MediaObject, media_id)
    media.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    key, bucket = media.object_key, media.bucket
    s.commit()
    s.close()

    from app.worker.tasks import cleanup_expired_scene_photos

    result = cleanup_expired_scene_photos.delay().get(timeout=30)
    assert result["purged"] >= 1

    from app.providers.factory import get_storage_provider

    assert get_storage_provider().stat_object(key, bucket) is None

    s = get_session_factory()()
    media = s.get(MediaObject, media_id)
    assert media.upload_status == "deleted"
    s.close()
