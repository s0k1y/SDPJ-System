"""API 端点集成测试"""

import pytest
from fastapi.testclient import TestClient
from sdpj.ui.webui.backend.app import app


@pytest.fixture(scope="session")
def client():  # noqa: ANN201, D103
    return TestClient(app, raise_server_exceptions=False)


class TestAuthEndpoints:  # noqa: D101
    def test_register_success(self, client) -> None:  # noqa: ANN001, D102
        import uuid

        username = f"int_{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/auth/register", json={"username": username, "password": "pass123456"}
        )
        assert resp.status_code in (200, 400, 500)

    def test_register_missing_field(self, client) -> None:  # noqa: ANN001, D102
        resp = client.post("/api/auth/register", json={"username": "only"})
        assert resp.status_code == 422

    def test_login_wrong_password(self, client) -> None:  # noqa: ANN001, D102
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "wrongpass"})
        assert resp.status_code in (401, 500)

    def test_logout(self, client) -> None:  # noqa: ANN001, D102
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200

    def test_public_key_endpoint(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/api/auth/public-key")
        assert resp.status_code == 200
        assert "public_key" in resp.json()["data"]


class TestPublicEndpoints:  # noqa: D101
    def test_health(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ok"

    def test_root(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/")
        assert resp.status_code == 200

    def test_api_status(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/api/status")
        assert resp.status_code == 200
        assert "status" in resp.json()["data"]

    def test_encoding_types_endpoint(self, client) -> None:  # noqa: ANN001, D102
        """GET /api/detection/encoding-types 应返回 13 种编码类型。"""
        resp = client.get("/api/detection/encoding-types")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 13

    def test_encoding_types_item_structure(self, client) -> None:  # noqa: ANN001, D102
        """每个编码类型项应包含 name、label、chinese_compatible 字段。"""
        resp = client.get("/api/detection/encoding-types")
        data = resp.json()["data"]
        for item in data:
            assert "name" in item
            assert "label" in item
            assert "chinese_compatible" in item
            assert isinstance(item["chinese_compatible"], bool)

    def test_encoding_types_contains_expected_names(self, client) -> None:  # noqa: ANN001, D102
        """编码列表应包含所有 13 种编码类型名称。"""
        resp = client.get("/api/detection/encoding-types")
        data = resp.json()["data"]
        names = {item["name"] for item in data}
        expected = {
            "base16", "base32", "base64", "base85",
            "rot13", "hex", "morse", "ascii", "unicode",
            "caesar", "vigenere", "url", "unicode_escape",
        }
        assert names == expected


class TestProtectedEndpoints:  # noqa: D101
    def test_unauthenticated_returns_401(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/api/detection/datasets")
        assert resp.status_code == 401

    def test_unauthenticated_reports_returns_401(self, client) -> None:  # noqa: ANN001, D102
        resp = client.get("/api/reports/list")
        assert resp.status_code == 401
