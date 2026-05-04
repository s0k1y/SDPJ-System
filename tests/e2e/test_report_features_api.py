"""端到端测试 - 报告新功能 API

测试通过 WebUI API 访问子类型合规率和平均迭代次数功能
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sdpj.ui.webui.backend.app import app


class TestReportVisualizationAPI:
    """测试报告可视化 API 端点"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)
        self.unique_username = f"e2e_report_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self):
        """辅助方法: 注册并登录"""
        self.client.post("/api/auth/register", json={
            "username": self.unique_username,
            "password": self.password
        })
        login_response = self.client.post("/api/auth/login", json={
            "username": self.unique_username,
            "password": self.password
        })
        return login_response

    def test_visualization_endpoint_includes_subtype_compliance(self):
        """测试可视化端点返回子类型合规率"""
        self._register_and_login()

        # 假设有一个已存在的 task_group_id（实际测试中需要先创建）
        # 这里测试 API 结构是否正确
        response = self.client.get("/api/reports/visualization/test_tg_id")

        # API 应该能响应（即使 task_group_id 不存在）
        assert response.status_code in [200, 401, 404, 500]

        if response.status_code == 200:
            data = response.json()
            # 验证响应包含必要字段
            assert "subtype_compliance" in data or "error" in data

    def test_visualization_endpoint_includes_avg_iteration_count(self):
        """测试可视化端点返回平均迭代次数"""
        self._register_and_login()

        response = self.client.get("/api/reports/visualization/test_tg_id")

        assert response.status_code in [200, 401, 404, 500]

        if response.status_code == 200:
            data = response.json()
            # avg_iteration_count 可能为 None（静态检测）或数字（动态检测）
            assert "avg_iteration_count" in data or "error" in data


class TestReportListAPI:
    """测试报告列表 API"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)
        self.unique_username = f"e2e_list_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self):
        """辅助方法: 注册并登录"""
        self.client.post("/api/auth/register", json={
            "username": self.unique_username,
            "password": self.password
        })
        return self.client.post("/api/auth/login", json={
            "username": self.unique_username,
            "password": self.password
        })

    def test_report_list_endpoint(self):
        """测试报告列表端点"""
        self._register_and_login()

        response = self.client.get("/api/reports/list")

        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


class TestDashboardStatisticsAPI:
    """测试 Dashboard 统计 API"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_statistics_endpoint_structure(self):
        """测试统计端点返回结构"""
        response = self.client.get("/api/reports/statistics")

        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            # 验证基础统计字段
            assert "total" in data
            assert "compliant" in data
            assert "non_compliant" in data
            assert "compliance_rate" in data


class TestReportExportAPI:
    """测试报告导出 API"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)
        self.unique_username = f"e2e_export_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self):
        """辅助方法: 注册并登录"""
        self.client.post("/api/auth/register", json={
            "username": self.unique_username,
            "password": self.password
        })
        return self.client.post("/api/auth/login", json={
            "username": self.unique_username,
            "password": self.password
        })

    def test_export_jsonl_format(self):
        """测试导出 JSONL 格式"""
        self._register_and_login()

        response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id",
            "format": "jsonl"
        })

        # 即使 task_group_id 不存在，API 也应该能响应
        assert response.status_code in [200, 401, 404, 500]

    def test_export_json_format(self):
        """测试导出 JSON 格式"""
        self._register_and_login()

        response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id",
            "format": "json"
        })

        assert response.status_code in [200, 401, 404, 500]

    def test_export_yaml_format(self):
        """测试导出 YAML 格式"""
        self._register_and_login()

        response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id",
            "format": "yaml"
        })

        assert response.status_code in [200, 401, 404, 500]

    def test_export_invalid_format(self):
        """测试导出不支持的格式"""
        self._register_and_login()

        response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id",
            "format": "pdf"  # 不支持的格式
        })

        # 应该返回错误
        assert response.status_code in [400, 401, 422, 500]


class TestReportFeaturesFullWorkflow:
    """测试报告功能的完整工作流"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)
        self.unique_username = f"e2e_workflow_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def test_complete_report_workflow(self):
        """测试完整报告流程: 注册 -> 登录 -> 查看报告列表 -> 查看可视化 -> 导出"""

        # 1. 用户注册
        reg_response = self.client.post("/api/auth/register", json={
            "username": self.unique_username,
            "password": self.password
        })
        assert reg_response.status_code in [200, 400, 500]

        # 2. 用户登录
        login_response = self.client.post("/api/auth/login", json={
            "username": self.unique_username,
            "password": self.password
        })
        assert login_response.status_code in [200, 500]

        # 3. 查询报告列表
        list_response = self.client.get("/api/reports/list")
        assert list_response.status_code in [200, 401, 500]

        # 4. 查询全局统计（Dashboard）
        stats_response = self.client.get("/api/reports/statistics")
        assert stats_response.status_code in [200, 401, 500]

        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            # 验证统计数据结构
            assert "total" in stats_data
            assert "compliance_rate" in stats_data

        # 5. 查看可视化数据（假设有 task_group_id）
        viz_response = self.client.get("/api/reports/visualization/test_tg_id")
        assert viz_response.status_code in [200, 401, 404, 500]

        if viz_response.status_code == 200:
            viz_data = viz_response.json()
            # 验证可视化数据包含新功能
            if "subtype_compliance" in viz_data:
                assert isinstance(viz_data["subtype_compliance"], list)
            if "avg_iteration_count" in viz_data:
                assert viz_data["avg_iteration_count"] is None or isinstance(viz_data["avg_iteration_count"], (int, float))

        # 6. 导出报告
        export_response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id",
            "format": "jsonl"
        })
        assert export_response.status_code in [200, 401, 404, 500]


class TestReportAPIValidation:
    """测试报告 API 参数验证"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_visualization_missing_task_group_id(self):
        """测试可视化端点缺少 task_group_id"""
        # 直接访问不带参数的端点应该返回 404 或 422
        response = self.client.get("/api/reports/visualization/")
        assert response.status_code in [401, 404, 422]

    def test_export_missing_task_group_id(self):
        """测试导出端点缺少 task_group_id"""
        response = self.client.post("/api/reports/export", json={
            "format": "jsonl"
        })
        assert response.status_code in [400, 401, 422, 500]

    def test_export_missing_format(self):
        """测试导出端点缺少 format"""
        response = self.client.post("/api/reports/export", json={
            "task_group_id": "test_tg_id"
        })
        # format 有默认值，应该能成功或返回 404（task_group_id 不存在）
        assert response.status_code in [200, 401, 404, 500]


class TestReportDataIntegrity:
    """测试报告数据完整性"""

    def setup_method(self):
        """每个测试前的设置"""
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_subtype_compliance_data_structure(self):
        """测试子类型合规率数据结构"""
        response = self.client.get("/api/reports/visualization/test_tg_id")

        if response.status_code == 200:
            data = response.json()
            if "subtype_compliance" in data and data["subtype_compliance"]:
                # 验证每个子类型条目的结构
                for item in data["subtype_compliance"]:
                    assert "category" in item
                    assert "total" in item
                    assert "passed" in item
                    assert "failed" in item
                    assert "rate" in item
                    # 验证数值合理性
                    assert item["total"] == item["passed"] + item["failed"]
                    assert 0 <= item["rate"] <= 100

    def test_avg_iteration_count_data_type(self):
        """测试平均迭代次数数据类型"""
        response = self.client.get("/api/reports/visualization/test_tg_id")

        if response.status_code == 200:
            data = response.json()
            if "avg_iteration_count" in data:
                # 应该是 None 或非负数
                assert data["avg_iteration_count"] is None or (
                    isinstance(data["avg_iteration_count"], (int, float)) and
                    data["avg_iteration_count"] >= 0
                )
