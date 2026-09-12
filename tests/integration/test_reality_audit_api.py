"""Reality Audit admin API (REALITY_AUDIT_PLAN / NEXT_GOAL §C2).

Same pure engine as the CLI, exposed for the Admin console. No DB writes:
samples stay request-scoped.
"""

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

REPO_DOCS = Path(__file__).resolve().parents[2] / "docs" / "reality_audit"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def moderator(client):
    email = f"ramod-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"display_name": "现实审计员", "email": email, "password": "passw0rd123"},
    )
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    u = s.query(User).filter(User.email == email).one()
    u.role = "admin"
    s.commit()
    s.close()
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    return tok


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def samples_payload():
    return json.loads((REPO_DOCS / "synthetic_samples.json").read_text(encoding="utf-8"))


def test_reality_audit_rejects_empty_samples(client, moderator):
    r = client.post("/api/v1/admin/reality-audit", json={"samples": []}, headers=_auth(moderator))
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "samples_required"


def test_reality_audit_runs_engine_over_synthetic_samples(client, moderator, samples_payload):
    r = client.post(
        "/api/v1/admin/reality-audit",
        json={"samples": samples_payload["samples"]},
        headers=_auth(moderator),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sample_count"] == 6
    assert body["expressible_count"] == 5
    kinds = {g["kind"] for g in body["schema_gaps"]}
    assert "note_only_condition" in kinds
    assert "unmodelled_coexistence_attribute" in kinds
    # 法定强制地板事件冲突被记录（syn-event-006）
    event = next(s for s in body["samples"] if s["sample_id"] == "syn-event-006")
    assert event["resolver_results"][0]["compliance_state"] == "POTENTIAL_CONFLICT"


def test_reality_audit_requires_moderator(client, samples_payload):
    email = f"rapl-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"display_name": "普通用户", "email": email, "password": "passw0rd123"},
    )
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    r = client.post(
        "/api/v1/admin/reality-audit",
        json={"samples": samples_payload["samples"]},
        headers=_auth(tok),
    )
    assert r.status_code in (401, 403)
