"""
认证 API 端点测试
"""

import uuid
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "server"))

from main import app

client = TestClient(app)


def _new_user_payload():
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"apitest_{suffix}",
        "email": f"apitest_{suffix}@example.com",
        "password": "secret123",
    }


def test_register_success():
    payload = _new_user_payload()
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800


def test_login_success():
    payload = _new_user_payload()
    register_resp = client.post("/auth/register", json=payload)
    assert register_resp.status_code == 200

    response = client.post(
        "/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    payload = _new_user_payload()
    register_resp = client.post("/auth/register", json=payload)
    assert register_resp.status_code == 200

    response = client.post(
        "/auth/login",
        json={"username": payload["username"], "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
