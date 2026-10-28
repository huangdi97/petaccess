"""Consumer privacy rights are real server transactions, never local fake success."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.audit_events import AuditEvent
from app.db.session import get_session_factory
from app.main import app
from app.models import AuditLog


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _register(client):
    email = f"privacy-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"display_name": "隐私权测试用户", "email": email, "password": "passw0rd123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"], email


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_export_is_user_scoped_and_excludes_secret_fields(client):
    token, email = _register(client)
    response = client.get("/api/v1/privacy/export", headers=_auth(token))
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["account"]["email"] == email
    assert "password_hash" not in body["account"]
    assert "object_key" not in response.text
    assert isinstance(body["pets"], list)
    assert isinstance(body["boundary_profiles"], list)
    assert isinstance(body["watches"], list)
    assert isinstance(body["contribution_activity"], list)
    assert isinstance(body["uploaded_media"], list)

    with get_session_factory()() as db:
        row = db.scalar(
            select(AuditLog).where(
                AuditLog.action == AuditEvent.PRIVACY_EXPORT.value,
                AuditLog.target_type == "user",
            )
        )
        assert row is not None


def test_account_deletion_request_is_persisted_and_idempotent(client):
    token, _ = _register(client)
    headers = _auth(token)

    initial = client.get("/api/v1/privacy/account-deletion-request", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["status"] == "none"

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    first = client.post("/api/v1/privacy/account-deletion-request", headers=headers)
    assert first.status_code == 202, first.text
    assert first.json()["status"] == "submitted"
    requested_at = first.json()["requested_at"]
    assert requested_at

    second = client.post("/api/v1/privacy/account-deletion-request", headers=headers)
    assert second.status_code == 202, second.text
    assert second.json()["status"] == "submitted"
    assert second.json()["requested_at"] == requested_at

    with get_session_factory()() as db:
        rows = db.scalars(
            select(AuditLog).where(
                AuditLog.action == AuditEvent.PRIVACY_ACCOUNT_DELETION_REQUEST.value,
                AuditLog.target_type == "user",
            )
        ).all()
        own_rows = [row for row in rows if row.target_id == user_id]
        assert len(own_rows) == 1
