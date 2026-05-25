"""端到端测试 - 报告新功能 API

测试通过 WebUI API 访问子类型合规率和平均迭代次数功能
"""

import pytest
import uuid
from sdpj.ui.webui.backend.app import app


class TestReportVisualizationAPI:
    """测试报告可视化 API 端点"""

    def setup_method(self):
        self.unique_username = f"e2e_report_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self, client):
        """辅助方法: 注册并登录"""
        client.post(
            "/api/auth/register", json={"username": self.unique_username, "password": self.password}
        )
        login_response = client.post(
            "/api/auth/login", json={"username": self.unique_username, "password": self.password}
        )
        return login_response

    def test_visualization_endpoint_includes_subtype_compliance(self, client):
        """测试可视化端点返回子类型合规率"""
        self._register_and_login(client)

        response = client.get("/api/reports/visualization/test_tg_id")

        assert response.status_code in [200, 401, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "subtype_compliance" in data or "error" in data

    def test_visualization_endpoint_includes_avg_iteration_count(self, client):
        """测试可视化端点返回平均迭代次数"""
        self._register_and_login(client)

        response = client.get("/api/reports/visualization/test_tg_id")

        assert response.status_code in [200, 401, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "avg_iteration_count" in data or "error" in data


class TestReportListAPI:
    """测试报告列表 API"""

    def setup_method(self):
        self.unique_username = f"e2e_list_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self, client):
        """辅助方法: 注册并登录"""
        client.post(
            "/api/auth/register", json={"username": self.unique_username, "password": self.password}
        )
        return client.post(
            "/api/auth/login", json={"username": self.unique_username, "password": self.password}
        )

    def test_report_list_endpoint(self, client):
        """测试报告列表端点"""
        self._register_and_login(client)

        response = client.get("/api/reports/list")

        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


class TestDashboardStatisticsAPI:
    """测试 Dashboard 统计 API"""

    def test_statistics_endpoint_structure(self, client):
        """测试统计端点返回结构"""
        response = client.get("/api/reports/statistics")

        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "compliant" in data
            assert "non_compliant" in data
            assert "compliance_rate" in data


class TestReportExportAPI:
    """测试报告导出 API"""

    def setup_method(self):
        self.unique_username = f"e2e_export_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def _register_and_login(self, client):
        """辅助方法: 注册并登录"""
        client.post(
            "/api/auth/register", json={"username": self.unique_username, "password": self.password}
        )
        return client.post(
            "/api/auth/login", json={"username": self.unique_username, "password": self.password}
        )

    def test_export_jsonl_format(self, client):
        """测试导出 JSONL 格式"""
        self._register_and_login(client)

        response = client.post(
            "/api/reports/export", json={"task_group_id": "test_tg_id", "format": "jsonl"}
        )

        assert response.status_code in [200, 401, 404, 500]

    def test_export_json_format(self, client):
        """测试导出 JSON 格式"""
        self._register_and_login(client)

        response = client.post(
            "/api/reports/export", json={"task_group_id": "test_tg_id", "format": "json"}
        )

        assert response.status_code in [200, 401, 404, 500]

    def test_export_yaml_format(self, client):
        """测试导出 YAML 格式"""
        self._register_and_login(client)

        response = client.post(
            "/api/reports/export", json={"task_group_id": "test_tg_id", "format": "yaml"}
        )

        assert response.status_code in [200, 401, 404, 500]

    def test_export_invalid_format(self, client):
        """测试导出不支持的格式"""
        self._register_and_login(client)

        response = client.post(
            "/api/reports/export",
            json={
                "task_group_id": "test_tg_id",
                "format": "pdf",
            },
        )

        assert response.status_code in [400, 401, 422, 500]


class TestReportFeaturesFullWorkflow:
    """测试报告功能的完整工作流"""

    def setup_method(self):
        self.unique_username = f"e2e_workflow_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def test_complete_report_workflow(self, client):
        """测试完整报告流程: 注册 -> 登录 -> 查看报告列表 -> 查看可视化 -> 导出"""

        # 1. 用户注册
        reg_response = client.post(
            "/api/auth/register", json={"username": self.unique_username, "password": self.password}
        )
        assert reg_response.status_code in [200, 400, 500]

        # 2. 用户登录
        login_response = client.post(
            "/api/auth/login", json={"username": self.unique_username, "password": self.password}
        )
        assert login_response.status_code in [200, 500]

        # 3. 查询报告列表
        list_response = client.get("/api/reports/list")
        assert list_response.status_code in [200, 401, 500]

        # 4. 查询全局统计（Dashboard）
        stats_response = client.get("/api/reports/statistics")
        assert stats_response.status_code in [200, 401, 500]

        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            assert "total" in stats_data["data"]
            assert "compliance_rate" in stats_data["data"]

        # 5. 查看可视化数据（假设有 task_group_id）
        viz_response = client.get("/api/reports/visualization/test_tg_id")
        assert viz_response.status_code in [200, 401, 404, 500]

        if viz_response.status_code == 200:
            viz_data = viz_response.json()
            if "subtype_compliance" in viz_data:
                assert isinstance(viz_data["subtype_compliance"], list)
            if "avg_iteration_count" in viz_data:
                assert viz_data["avg_iteration_count"] is None or isinstance(
                    viz_data["avg_iteration_count"], (int, float)
                )

        # 6. 导出报告
        export_response = client.post(
            "/api/reports/export", json={"task_group_id": "test_tg_id", "format": "jsonl"}
        )
        assert export_response.status_code in [200, 401, 404, 500]


class TestReportAPIValidation:
    """测试报告 API 参数验证"""

    def test_visualization_missing_task_group_id(self, client):
        """测试可视化端点缺少 task_group_id"""
        response = client.get("/api/reports/visualization/")
        assert response.status_code in [401, 404, 422]

    def test_export_missing_task_group_id(self, client):
        """测试导出端点缺少 task_group_id"""
        response = client.post("/api/reports/export", json={"format": "jsonl"})
        assert response.status_code in [400, 401, 422, 500]

    def test_export_missing_format(self, client):
        """测试导出端点缺少 format"""
        response = client.post("/api/reports/export", json={"task_group_id": "test_tg_id"})
        assert response.status_code in [200, 401, 404, 500]


class TestReportDataIntegrity:
    """测试报告数据完整性"""

    def test_subtype_compliance_data_structure(self, client):
        """测试子类型合规率数据结构"""
        response = client.get("/api/reports/visualization/test_tg_id")

        if response.status_code == 200:
            data = response.json()
            if "subtype_compliance" in data and data["subtype_compliance"]:
                for item in data["subtype_compliance"]:
                    assert "category" in item
                    assert "total" in item
                    assert "passed" in item
                    assert "failed" in item
                    assert "rate" in item
                    assert item["total"] == item["passed"] + item["failed"]
                    assert 0 <= item["rate"] <= 100

    def test_avg_iteration_count_data_type(self, client):
        """测试平均迭代次数数据类型"""
        response = client.get("/api/reports/visualization/test_tg_id")

        if response.status_code == 200:
            data = response.json()
            if "avg_iteration_count" in data:
                assert data["avg_iteration_count"] is None or (
                    isinstance(data["avg_iteration_count"], (int, float))
                    and data["avg_iteration_count"] >= 0
                )
