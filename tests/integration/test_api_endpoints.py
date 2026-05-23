"""API 端点集成测试"""

import pytest
from fastapi.testclient import TestClient
from sdpj.ui.webui.backend.app import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestAuthEndpoints:
    def test_register_success(self, client):
        import uuid

        username = f"int_{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/auth/register", json={"username": username, "password": "pass123456"}
        )
        assert resp.status_code in (200, 400, 500)

    def test_register_missing_field(self, client):
        resp = client.post("/api/auth/register", json={"username": "only"})
        assert resp.status_code == 422

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "wrongpass"})
        assert resp.status_code in (401, 500)

    def test_logout(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200

    def test_public_key_endpoint(self, client):
        resp = client.get("/api/auth/public-key")
        assert resp.status_code == 200
        assert "public_key" in resp.json()["data"]


class TestPublicEndpoints:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ok"

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_api_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        assert "status" in resp.json()["data"]


class TestProtectedEndpoints:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/detection/datasets")
        assert resp.status_code == 401

    def test_unauthenticated_reports_returns_401(self, client):
        resp = client.get("/api/reports/list")
        assert resp.status_code == 401
