"""Consumer AI endpoints must never surface deterministic mock output as real advice."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _headers(client: TestClient) -> dict[str, str]:
    token = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "AI fail-closed test",
            "email": f"ai-fail-closed-{uuid.uuid4().hex[:8]}@example.com",
            "password": "passw0rd123",
        },
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_pet_vision_does_not_return_hash_based_mock_suggestion(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/pet-vision",
        headers=_headers(client),
        files={"image": ("pet.jpg", b"not-a-real-photo", "image/jpeg")},
    )
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "provider_unavailable"
    assert "柴犬" not in response.text
    assert "柯基" not in response.text


def test_ocr_does_not_return_canned_signage_as_evidence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/ocr-signage",
        headers=_headers(client),
        files={"image": ("sign.jpg", b"not-a-real-sign", "image/jpeg")},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"
    assert "本店允许携带宠物" not in response.text


def test_natural_language_parser_does_not_return_mock_draft(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/parse-query",
        headers=_headers(client),
        json={"text": "附近允许犬进入的咖啡店"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"
    assert "search_places" not in response.text
