"""Wave 4 完整集成测试"""
import pytest
from fastapi.testclient import TestClient


class TestCLI:
    """CLI 集成测试"""

    def test_cli_module_exists(self):
        """测试 CLI 模块存在"""
        import os
        cli_path = "sdpj/ui/cli.py"
        assert os.path.exists(cli_path)


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

    def test_api_routes_count(self):
        """测试 API 路由数量"""
        from sdpj.ui.webui_backend import app
        routes = [route.path for route in app.routes]
        # 至少应该有核心路由
        assert len(routes) >= 8


class TestWebUIFrontend:
    """WebUI Frontend 集成测试"""

    def test_frontend_structure(self):
        """测试前端目录结构"""
        import os
        
        base_path = "sdpj/ui/webui-frontend"
        assert os.path.exists(base_path)
        
        # 检查关键文件
        assert os.path.exists(f"{base_path}/package.json")
        assert os.path.exists(f"{base_path}/vite.config.ts")
        assert os.path.exists(f"{base_path}/index.html")
        assert os.path.exists(f"{base_path}/src/App.tsx")
        assert os.path.exists(f"{base_path}/src/main.tsx")

    def test_frontend_components(self):
        """测试前端组件"""
        import os
        
        components_path = "sdpj/ui/webui-frontend/src/components"
        assert os.path.exists(f"{components_path}/AppHeader.tsx")
        assert os.path.exists(f"{components_path}/AppSidebar.tsx")

    def test_frontend_pages(self):
        """测试前端页面"""
        import os
        
        pages_path = "sdpj/ui/webui-frontend/src/pages"
        assert os.path.exists(f"{pages_path}/Dashboard.tsx")
        assert os.path.exists(f"{pages_path}/Detection.tsx")
        assert os.path.exists(f"{pages_path}/Reports.tsx")
        assert os.path.exists(f"{pages_path}/Login.tsx")

    def test_frontend_services(self):
        """测试前端服务层"""
        import os
        
        services_path = "sdpj/ui/webui-frontend/src/services"
        assert os.path.exists(f"{services_path}/api.ts")

    def test_frontend_types(self):
        """测试前端类型定义"""
        import os
        
        types_path = "sdpj/ui/webui-frontend/src/types"
        assert os.path.exists(f"{types_path}/index.ts")
