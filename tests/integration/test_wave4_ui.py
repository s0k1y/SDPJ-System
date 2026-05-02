"""Wave 4 用户界面层集成测试"""
import pytest
from fastapi.testclient import TestClient


class TestCLI:
    """CLI 集成测试"""

    def test_cli_import(self):
        """测试 CLI 导入"""
        # CLI 是目录，导入模块
        import sys
        sys.path.insert(0, '.')
        from sdpj.ui import cli as cli_module
        assert cli_module is not None


class TestWebUIBackend:
    """WebUI Backend 集成测试"""

    def test_backend_import(self):
        """测试 Backend 导入"""
        from sdpj.ui.webui_backend import app
        assert app is not None

    def test_root_endpoint(self):
        """测试根路径"""
        from sdpj.ui.webui_backend import app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "SDPJ-System API" in response.json()["message"]

    def test_status_endpoint(self):
        """测试状态查询"""
        from sdpj.ui.webui_backend import app
        client = TestClient(app)
        response = client.get("/api/status")
        assert response.status_code == 200
        assert "status" in response.json()

    @pytest.mark.asyncio
    async def test_register_endpoint(self):
        """测试注册接口"""
        from sdpj.ui.webui_backend import app
        client = TestClient(app)
        
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code in [200, 400]  # 可能已存在

    def test_api_routes(self):
        """测试 API 路由完整性"""
        from sdpj.ui.webui_backend import app
        
        routes = [route.path for route in app.routes]
        
        # 检查关键路由
        assert "/" in routes
        assert "/api/status" in routes
        assert "/api/auth/register" in routes
        assert "/api/auth/login" in routes
        assert "/api/detection/start" in routes
