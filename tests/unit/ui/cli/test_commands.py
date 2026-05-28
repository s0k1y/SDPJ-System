"""
CLI 命令单元测试

覆盖:
1. Schema 验证
2. unwrap() 结果处理
3. CLI 命令调用 scheduler 方法(Mock StateSchedulerInterface)
"""

import click
import pytest
from click.testing import CliRunner
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock, patch

from sdpj.ui.cli.main import CLIContext, cli
from sdpj.ui.cli.schemas import (
    DetectionStartParams,
    ReportExportParams,
    AuthParams,
)
from sdpj.ui.cli.utils.result import unwrap
from tests.fixtures.sample_data import REAL_MODEL_ID
from typing import Any


# ═══════════════════════════════════════════════════════════
# Schema 验证测试
# ═══════════════════════════════════════════════════════════


class TestDetectionStartParams:
    """测试 TestDetectionStartParams 类."""

    def test_valid_string_model_id(self) -> None:
        """测试 test valid string model id."""
        p = DetectionStartParams(model_id="deepseek-v4-pro", dataset_ids=[1, 2])
        assert p.model_id == "deepseek-v4-pro"

    def test_valid_int_model_id(self) -> None:
        """测试 test valid int model id."""
        p = DetectionStartParams(model_id=42, dataset_ids=[1])
        assert p.model_id == 42

    def test_defaults(self) -> None:
        """测试 test defaults."""
        p = DetectionStartParams(model_id="test")
        assert p.dataset_ids == []
        assert p.config_id is None
        assert p.force_refresh is False

    def test_missing_required_model_id(self) -> None:
        """测试 test missing required model id."""
        with pytest.raises(ValidationError):
            DetectionStartParams(dataset_ids=[1])


class TestReportExportParams:
    """测试 TestReportExportParams 类."""

    def test_with_task_id(self) -> None:
        """测试 test with task id."""
        p = ReportExportParams(task_group_id="tg-001", target_format="json", task_id="task-1")
        assert p.task_id == "task-1"

    def test_without_task_id(self) -> None:
        """测试 test without task id."""
        p = ReportExportParams(task_group_id="tg-001", target_format="yaml")
        assert p.task_id is None

    def test_default_format(self) -> None:
        """测试 test default format."""
        p = ReportExportParams(task_group_id="tg-001")
        assert p.target_format == "json"


class TestAuthParams:
    """测试 TestAuthParams 类."""

    def test_valid(self) -> None:
        """测试 test valid."""
        p = AuthParams(username="alice", password="secret123")
        assert p.username == "alice"

    def test_missing_password(self) -> None:
        """测试 test missing password."""
        with pytest.raises(ValidationError):
            AuthParams(username="alice")


# ═══════════════════════════════════════════════════════════
# unwrap() 测试
# ═══════════════════════════════════════════════════════════


class TestUnwrap:
    """测试 TestUnwrap 类."""

    def test_success_strips_wrapper(self) -> None:
        """测试 test success strips wrapper."""
        data = unwrap({"success": True, "task_group_id": "tg-001", "task_ids": ["t1"]})
        assert data == {"task_group_id": "tg-001", "task_ids": ["t1"]}

    def test_failure_raises_click_exception(self) -> None:
        """测试 test failure raises click exception."""
        with pytest.raises(click.ClickException, match="测试错误"):
            unwrap({"success": False, "error": "测试错误"})

    def test_failure_fallback_to_message(self) -> None:
        """测试 test failure fallback to message."""
        with pytest.raises(click.ClickException, match="失败原因"):
            unwrap({"success": False, "message": "失败原因"})

    def test_failure_default_message(self) -> None:
        """测试 test failure default message."""
        with pytest.raises(click.ClickException, match="操作失败"):
            unwrap({"success": False})

    def test_required_field_present(self) -> None:
        """测试 test required field present."""
        data = unwrap({"success": True, "report": {"id": 1}}, required="report")
        assert "report" in data

    def test_required_field_missing(self) -> None:
        """测试 test required field missing."""
        with pytest.raises(click.ClickException, match="缺少必要字段"):
            unwrap({"success": True, "data": {}}, required="report")


# ═══════════════════════════════════════════════════════════
# Mock 辅助
# ═══════════════════════════════════════════════════════════


def _make_mock_scheduler() -> None:
    """测试 make mock scheduler."""
    s = MagicMock()
    s.session_init = AsyncMock()
    s.startup = AsyncMock()
    s.start_detection = AsyncMock()
    s.query_detection_progress = AsyncMock()
    s.execute_concurrent_tasks = AsyncMock()
    s.cancel_task = AsyncMock()
    s.cancel_task_group = AsyncMock()
    s.query_available_datasets = AsyncMock()
    s.query_dataset_detail = AsyncMock()
    s.export_dataset_file = AsyncMock()
    s.import_dataset_file = AsyncMock()
    s.delete_user_dataset = AsyncMock()

    s.generate_report = AsyncMock()
    s.view_report = AsyncMock()
    s.list_reports = AsyncMock()
    s.delete_report = AsyncMock()
    s.export_report = AsyncMock()
    s.query_compliance_statistics = AsyncMock()
    s.prepare_visualization_data = AsyncMock()
    s.prepare_task_visualization_data = AsyncMock()

    s.schedule_user_auth = AsyncMock()
    s.schedule_account_operation = AsyncMock()
    s.schedule_dac_operation = AsyncMock()
    s.list_all_users = AsyncMock()
    s.query_logs = AsyncMock()

    s.schedule_config_operation = AsyncMock()
    s.schedule_private_resource_operation = AsyncMock()
    s.check_resource_access = AsyncMock()

    s.subscribe_llm_calls = MagicMock()
    s.unsubscribe_llm_calls = MagicMock()
    return s


def _invoke(args: list[str], scheduler: Any, *, user_id: int = 1) -> None:
    """调用 CLI 命令,以 Mock scheduler 和已登录用户跑"""
    runner = CliRunner()
    with (
        patch("sdpj.ui.cli.main._bootstrap", return_value=scheduler),
        patch("sdpj.ui.cli.main.load_session", return_value=user_id),
        patch.object(CLIContext, "require_login", return_value=user_id),
    ):
        return runner.invoke(cli, args)


def _invoke_logout(args: list[str], scheduler: Any) -> None:
    """调用 CLI 命令,未登录状态"""
    runner = CliRunner()
    with (
        patch("sdpj.ui.cli.main._bootstrap", return_value=scheduler),
        patch("sdpj.ui.cli.main.load_session", return_value=None),
    ):
        return runner.invoke(cli, args)


# ═══════════════════════════════════════════════════════════
# Detect task 命令
# ═══════════════════════════════════════════════════════════


class TestDetectStart:
    """测试 TestDetectStart 类."""

    def test_start_basic(self) -> None:
        """测试 test start basic."""
        s = _make_mock_scheduler()
        s.start_detection.return_value = {
            "success": True,
            "task_group_id": "tg-001",
            "task_ids": ["t1", "t2"],
        }
        result = _invoke(
            [
                "Detect",
                "task",
                "start",
                "--model-id",
                "deepseek",
                "--dataset",
                "1",
                "--dataset",
                "2",
                "--type", "static",
                "--config-id", "1",
                "--attack-path", "direct",
            ],
            s,
        )
        assert result.exit_code == 0
        config_data = s.start_detection.call_args[0][1]
        assert config_data["dataset_ids"] == [1, 2]

    def test_start_with_int_model_id(self) -> None:
        """测试 test start with int model id."""
        s = _make_mock_scheduler()
        s.start_detection.return_value = {
            "success": True,
            "task_group_id": "tg-002",
            "task_ids": ["t1"],
        }
        result = _invoke(["Detect", "task", "start", "--model-id", "42", "--dataset", "1", "--type", "static", "--config-id", "1", "--attack-path", "direct"], s)
        assert result.exit_code == 0
        assert s.start_detection.call_args[0][1]["model_id"] == 42

    def test_start_force_refresh(self) -> None:
        """测试 test start force refresh."""
        s = _make_mock_scheduler()
        s.start_detection.return_value = {
            "success": True,
            "task_group_id": "tg-003",
            "task_ids": [],
        }
        result = _invoke(
            [
                "Detect",
                "task",
                "start",
                "--model-id",
                "ds",
                "--dataset",
                "1",
                "--type", "static",
                "--config-id", "1",
                "--force-refresh",
                "--jailbreak-dataset",
                "5",
                "--attack-path", "direct",
            ],
            s,
        )
        assert result.exit_code == 0
        config = s.start_detection.call_args[0][1]
        assert config["force_refresh"] is True
        assert config["jailbreak_dataset_ids"] == [5]

    def test_start_failure_shows_error(self) -> None:
        """测试 test start failure shows error."""
        s = _make_mock_scheduler()
        s.start_detection.return_value = {"success": False, "error": "模型未注册"}
        result = _invoke(["Detect", "task", "start", "--model-id", "bad", "--dataset", "1", "--type", "static", "--config-id", "1", "--attack-path", "direct"], s)
        assert result.exit_code == 1
        assert "模型未注册" in result.output

    def test_requires_login(self) -> None:
        """测试 test requires login."""
        s = _make_mock_scheduler()
        result = _invoke_logout(["Detect", "task", "start", "--model-id", "x", "--dataset", "1", "--type", "static", "--config-id", "1", "--attack-path", "direct"], s)
        assert result.exit_code == 1
        assert "登录" in result.output


class TestDetectCancel:
    """测试 TestDetectCancel 类."""

    def test_cancel_task(self) -> None:
        """测试 test cancel task."""
        s = _make_mock_scheduler()
        s.cancel_task.return_value = {"success": True}
        result = _invoke(["Detect", "task", "cancel", "--task-id", "t1"], s)
        assert result.exit_code == 0
        s.cancel_task.assert_called_once_with("t1")

    def test_cancel_group(self) -> None:
        """测试 test cancel group."""
        s = _make_mock_scheduler()
        s.cancel_task_group.return_value = {"success": True}
        result = _invoke(["Detect", "task", "cancel", "--group-id", "g1"], s)
        assert result.exit_code == 0
        s.cancel_task_group.assert_called_once_with("g1")

    def test_cancel_no_target(self) -> None:
        """测试 test cancel no target."""
        s = _make_mock_scheduler()
        result = _invoke(["Detect", "task", "cancel"], s)
        assert result.exit_code == 0
        assert "必须提供" in result.output


# ═══════════════════════════════════════════════════════════
# Detect dataset 命令
# ═══════════════════════════════════════════════════════════


class TestDetectDatasets:
    """测试 TestDetectDatasets 类."""

    def test_list_datasets(self) -> None:
        """测试 test list datasets."""
        s = _make_mock_scheduler()
        s.query_available_datasets = AsyncMock(
            return_value=[
                {"id": 1, "name": "jailbreak_llm", "risk_type": "jailbreak"},
            ]
        )
        result = _invoke(["Config", "dataset", "list"], s)
        assert result.exit_code == 0
        assert "jailbreak_llm" in result.output

    def test_list_empty(self) -> None:
        """测试 test list empty."""
        s = _make_mock_scheduler()
        s.query_available_datasets = AsyncMock(return_value=[])
        result = _invoke(["Config", "dataset", "list"], s)
        assert result.exit_code == 0
        assert "暂无" in result.output


class TestDetectDatasetDetail:
    """测试 TestDetectDatasetDetail 类."""

    def test_detail(self) -> None:
        """测试 test detail."""
        s = _make_mock_scheduler()
        s.query_dataset_detail = AsyncMock(
            return_value={"dataset_id": 1, "name": "jailbreak_llm", "risk_type": "jailbreak"}
        )
        result = _invoke(["Config", "dataset", "detail", "--id", "1"], s)
        assert result.exit_code == 0
        s.query_dataset_detail.assert_called_once_with(1, user_id=1)

    def test_detail_not_found(self) -> None:
        """测试 test detail not found."""
        s = _make_mock_scheduler()
        s.query_dataset_detail = AsyncMock(return_value=None)
        result = _invoke(["Config", "dataset", "detail", "--id", "999"], s)
        assert result.exit_code == 0
        assert "不存在" in result.output


class TestDetectDatasetExport:
    """测试 TestDetectDatasetExport 类."""

    def test_export(self) -> None:
        """测试 test export."""
        s = _make_mock_scheduler()
        s.export_dataset_file = AsyncMock(
            return_value={"content": b"test", "filename": "dataset_1.jsonl"}
        )
        result = _invoke(["Config", "export-dataset", "--id", "1"], s)
        assert result.exit_code == 0
        assert "已导出" in result.output

    def test_export_not_found(self) -> None:
        """测试 test export not found."""
        s = _make_mock_scheduler()
        s.export_dataset_file = AsyncMock(return_value=None)
        result = _invoke(["Config", "export-dataset", "--id", "999"], s)
        assert result.exit_code == 0
        assert "不存在" in result.output


# ═══════════════════════════════════════════════════════════
# Report 命令
# ═══════════════════════════════════════════════════════════


class TestReportExport:
    """测试 TestReportExport 类."""

    def test_export_passes_task_id(self) -> None:
        """测试 test export passes task id."""
        s = _make_mock_scheduler()
        s.export_report.return_value = {"success": True, "filename": "report.json", "content": "x"}
        result = _invoke(
            ["Report", "export", "--group-id", "tg-001", "--format", "json", "--task-id", "task-1"],
            s,
        )
        assert result.exit_code == 0
        assert s.export_report.call_args[1]["task_id"] == "task-1"

    def test_export_without_task_id(self) -> None:
        """测试 test export without task id."""
        s = _make_mock_scheduler()
        s.export_report.return_value = {"success": True, "filename": "report.json", "content": "x"}
        result = _invoke(["Report", "export", "--group-id", "tg-001"], s)
        assert result.exit_code == 0
        assert s.export_report.call_args[1]["task_id"] is None


class TestReportGenerate:
    """测试 TestReportGenerate 类."""

    def test_generate_static_report(self) -> None:
        """测试 test generate static report."""
        s = _make_mock_scheduler()
        s.generate_report.return_value = {"success": True, "report": {"task_group_id": "tg-001"}}
        result = _invoke(["Report", "generate", "--group-id", "tg-001"], s)
        assert result.exit_code == 0
        assert "报告已生成" in result.output


class TestReportDelete:
    """测试 TestReportDelete 类."""

    def test_delete_success(self) -> None:
        """测试 test delete success."""
        s = _make_mock_scheduler()
        s.delete_report.return_value = {"success": True}
        result = _invoke(["Report", "delete", "--target-id", "tg-001"], s)
        assert result.exit_code == 0
        s.delete_report.assert_called_once_with("tg-001", 1, "task_group")


class TestReportView:
    """测试 TestReportView 类."""

    def test_view(self) -> None:
        """测试 test view."""
        s = _make_mock_scheduler()
        s.view_report = AsyncMock(
            return_value={
                "success": True,
                "report": {"task_group_id": "tg-001", "status": "completed"},
            }
        )
        result = _invoke(["Report", "view", "--group-id", "tg-001"], s)
        assert result.exit_code == 0
        s.view_report.assert_called_once_with("tg-001", user_id=1)


class TestReportList:
    """测试 TestReportList 类."""

    def test_list(self) -> None:
        """测试 test list."""
        s = _make_mock_scheduler()
        s.list_reports = AsyncMock(
            return_value=[
                {"task_group_id": "tg-001", "model_id": "deepseek", "status": "completed"},
            ]
        )
        result = _invoke(["Report", "list"], s)
        assert result.exit_code == 0
        assert "deepseek" in result.output

    def test_list_empty(self) -> None:
        """测试 test list empty."""
        s = _make_mock_scheduler()
        s.list_reports = AsyncMock(return_value=[])
        result = _invoke(["Report", "list"], s)
        assert result.exit_code == 0
        assert "暂无" in result.output

    def test_list_filter_by_model(self) -> None:
        """测试 test list filter by model."""
        s = _make_mock_scheduler()
        s.list_reports = AsyncMock(return_value=[])
        result = _invoke(["Report", "list", "--model-id", "deepseek"], s)
        assert result.exit_code == 0
        s.list_reports.assert_called_once_with({"user_id": 1, "model_id": "deepseek"})


class TestReportStatistics:
    """测试 TestReportStatistics 类."""

    def test_statistics(self) -> None:
        """测试 test statistics."""
        s = _make_mock_scheduler()
        s.query_compliance_statistics = AsyncMock(
            return_value={"success": True, "total_samples": 100, "passed": 80, "failed": 20}
        )
        result = _invoke(["Report", "statistics"], s)
        assert result.exit_code == 0


class TestReportVisualization:
    """测试 TestReportVisualization 类."""

    def test_visualization(self) -> None:
        """测试 test visualization."""
        s = _make_mock_scheduler()
        s.prepare_visualization_data = AsyncMock(
            return_value={"success": True, "data": {"risk_distribution": {}}}
        )
        result = _invoke(["Report", "visualization", "--group-id", "tg-001"], s)
        assert result.exit_code == 0

    def test_task_visualization(self) -> None:
        """测试 test task visualization."""
        s = _make_mock_scheduler()
        s.prepare_task_visualization_data = AsyncMock(
            return_value={"success": True, "data": {"risk_distribution": {}}}
        )
        result = _invoke(["Report", "visualization", "--task-id", "task-001"], s)
        assert result.exit_code == 0


# ═══════════════════════════════════════════════════════════
# User 命令
# ═══════════════════════════════════════════════════════════


class TestUserAuth:
    """测试 TestUserAuth 类."""

    def test_register_success(self) -> None:
        """测试 test register success."""
        s = _make_mock_scheduler()
        s.schedule_user_auth.return_value = {"success": True, "user_id": 5, "message": "注册成功"}
        result = _invoke(["User", "register", "--username", "alice", "--password", "pass123"], s)
        assert "注册成功" in result.output

    def test_login_sets_user_id(self) -> None:
        """测试 test login sets user id."""
        s = _make_mock_scheduler()
        s.schedule_user_auth.return_value = {"success": True, "user_id": 7}
        result = _invoke(["User", "login", "--username", "alice", "--password", "pass123"], s)
        assert result.exit_code == 0
        assert "7" in result.output

    def test_login_failure(self) -> None:
        """测试 test login failure."""
        s = _make_mock_scheduler()
        s.schedule_user_auth.return_value = {"success": False, "message": "密码错误"}
        result = _invoke(["User", "login", "--username", "alice", "--password", "wrong"], s)
        assert result.exit_code == 1
        assert "密码错误" in result.output


class TestUserLogout:
    """测试 TestUserLogout 类."""

    def test_logout(self) -> None:
        """测试 test logout."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(return_value={"success": True})
        result = _invoke(["User", "logout"], s)
        assert result.exit_code == 0
        assert "已登出" in result.output
        s.schedule_account_operation.assert_called_once_with("logout", {"user_id": 1})


class TestUserAccountOps:
    """测试 TestUserAccountOps 类."""

    def test_profile(self) -> None:
        """测试 test profile."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(
            return_value={"success": True, "profile": {"user_id": 1, "username": "alice"}}
        )
        result = _invoke(["User", "profile"], s)
        assert result.exit_code == 0
        assert "alice" in result.output

    def test_password(self) -> None:
        """测试 test password."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(return_value={"success": True})
        result = _invoke(["User", "password", "--old", "oldp", "--new", "newp"], s)
        assert result.exit_code == 0
        call_args = s.schedule_account_operation.call_args
        assert call_args[0][0] == "change_password"

    def test_switch(self) -> None:
        """测试 test switch."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(return_value={"success": True, "user_id": 9})
        result = _invoke(["User", "switch", "--username", "bob", "--password", "bobpass"], s)
        assert result.exit_code == 0
        assert "9" in result.output

    def test_unregister(self) -> None:
        """测试 test unregister."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(return_value={"success": True})
        result = _invoke(["User", "unregister", "--yes"], s)
        assert result.exit_code == 0

    def test_resources(self) -> None:
        """测试 test resources."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(
            return_value={
                "success": True,
                "resources": [{"resource_id": 1, "resource_type": "dataset", "dataset_name": "test"}],
                "shared_resources": [],
            }
        )
        result = _invoke(["User", "resources"], s)
        assert result.exit_code == 0
        assert "test" in result.output

    def test_list_users(self) -> None:
        """测试 test list users."""
        s = _make_mock_scheduler()
        s.list_all_users = AsyncMock(
            return_value=[{"user_id": 1, "username": "alice", "created_at": "2026-01-01"}]
        )
        result = _invoke(["User", "list"], s)
        assert result.exit_code == 0
        assert "alice" in result.output

    def test_list_users_empty(self) -> None:
        """测试 test list users empty."""
        s = _make_mock_scheduler()
        s.list_all_users = AsyncMock(return_value=[])
        result = _invoke(["User", "list"], s)
        assert result.exit_code == 0
        assert "暂无" in result.output

    def test_delete_user(self) -> None:
        """测试 test delete user."""
        s = _make_mock_scheduler()
        s.schedule_account_operation = AsyncMock(
            return_value={"success": True, "message": "用户已删除"}
        )
        result = _invoke(["User", "delete-user", "--user-id", "99", "--yes"], s)
        assert result.exit_code == 0


class TestDACCheck:
    """测试 TestDACCheck 类."""

    def test_check_access_granted(self) -> None:
        """测试 test check access granted."""
        s = _make_mock_scheduler()
        s.check_resource_access.return_value = True
        result = _invoke(["User", "auth", "check", "--resource-id", "42"], s)
        assert result.exit_code == 0
        assert "有访问权限" in result.output
        s.check_resource_access.assert_called_once_with(42, 1)

    def test_check_access_denied(self) -> None:
        """测试 test check access denied."""
        s = _make_mock_scheduler()
        s.check_resource_access.return_value = False
        result = _invoke(["User", "auth", "check", "--resource-id", "99"], s)
        assert result.exit_code == 0
        assert "无访问权限" in result.output


class TestDACOps:
    """测试 TestDACOps 类."""

    def test_grant(self) -> None:
        """测试 test grant."""
        s = _make_mock_scheduler()
        s.schedule_dac_operation = AsyncMock(return_value={"success": True, "message": "已授权"})
        result = _invoke(
            ["User", "auth", "grant", "--resource-id", "10", "--target-username", "bob"], s
        )
        assert result.exit_code == 0

    def test_revoke(self) -> None:
        """测试 test revoke."""
        s = _make_mock_scheduler()
        s.schedule_dac_operation = AsyncMock(return_value={"success": True, "message": "已移除"})
        result = _invoke(["User", "auth", "revoke", "--acl-id", "5"], s)
        assert result.exit_code == 0

    def test_show_acl(self) -> None:
        """测试 test show acl."""
        s = _make_mock_scheduler()
        s.schedule_dac_operation = AsyncMock(
            return_value={
                "success": True,
                "acl_list": [{"acl_id": 1, "grantee_user_id": 2, "grantee_username": "bob"}],
            }
        )
        result = _invoke(["User", "auth", "show", "--resource-id", "10"], s)
        assert result.exit_code == 0
        assert "bob" in result.output

    def test_show_acl_empty(self) -> None:
        """测试 test show acl empty."""
        s = _make_mock_scheduler()
        s.schedule_dac_operation = AsyncMock(return_value={"success": True, "acl_list": []})
        result = _invoke(["User", "auth", "show", "--resource-id", "10"], s)
        assert result.exit_code == 0
        assert "暂无" in result.output


# ═══════════════════════════════════════════════════════════
# Config 命令
# ═══════════════════════════════════════════════════════════


class TestConfigOps:
    """测试 TestConfigOps 类."""

    def test_create(self) -> None:
        """测试 test create."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={"success": True, "config_id": 7, "message": ""}
        )
        with (
            patch("sdpj.ui.cli.main._bootstrap", return_value=s),
            patch.object(CLIContext, "require_login", return_value=1),
        ):
            result = CliRunner().invoke(
                cli,
                [
                    "Config",
                    "create",
                    "--model",
                    "deepseek-v4-pro",
                    "--request-format",
                    "openai",
                    "--api-key",
                    "sk-95033b3c11914e7484298d3b736f2d95",
                    "--base-url",
                    "https://api.deepseek.com",
                    "--timeout",
                    "60",
                    "--max-rps",
                    "5",
                    "--max-concurrency",
                    "10",
                ],
            )
        assert result.exit_code == 0
        assert "7" in result.output

    def test_list(self) -> None:
        """测试 test list."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={
                "success": True,
                "configs": [
                    {
                        "config_id": 1,
                        "content": {"model_id": "deepseek-v4-pro", "request_format": "openai"},
                    }
                ],
            }
        )
        result = _invoke(["Config", "list"], s)
        assert result.exit_code == 0
        assert "deepseek-v4-pro" in result.output

    def test_list_empty(self) -> None:
        """测试 test list empty."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(return_value={"success": True, "configs": []})
        result = _invoke(["Config", "list"], s)
        assert result.exit_code == 0
        assert "暂无" in result.output

    def test_view(self) -> None:
        """测试 test view."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={"success": True, "config": {"id": 1, "model_id": REAL_MODEL_ID}}
        )
        result = _invoke(["Config", "view", "--config-id", "1"], s)
        assert result.exit_code == 0

    def test_verify(self) -> None:
        """测试 test verify."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={
                "success": True,
                "result": {
                    "status": "ok",
                    "model": "deepseek-v4-pro",
                    "latency_ms": 150,
                    "response_preview": "OK",
                },
            }
        )
        result = _invoke(["Config", "verify", "--config-id", "1"], s)
        assert result.exit_code == 0
        assert "连接正常" in result.output

    def test_delete(self) -> None:
        """测试 test delete."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(return_value={"success": True})
        result = _invoke(["Config", "delete", "--config-id", "1", "--yes"], s)
        assert result.exit_code == 0

    def test_export(self) -> None:
        """测试 test export."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={"success": True, "content": '{"key":"val"}'}
        )
        result = _invoke(["Config", "export", "--config-id", "1"], s)
        assert result.exit_code == 0
        assert '"key":"val"' in result.output

    def test_import(self) -> None:
        """测试 test import."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(
            return_value={"success": True, "config_id": 8, "message": ""}
        )
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("import_cfg.json", "w", encoding="utf-8") as f:
                f.write(
                    '{"model":"deepseek-v4-pro","request_format":"openai","api_key":"sk-95033b3c11914e7484298d3b736f2d95","base_url":"https://api.deepseek.com","timeout":60,"max_rps":5,"max_concurrency":10}'
                )
            with (
                patch("sdpj.ui.cli.main._bootstrap", return_value=s),
                patch.object(CLIContext, "require_login", return_value=1),
            ):
                result = runner.invoke(cli, ["Config", "import", "import_cfg.json"])
            assert result.exit_code == 0
            assert "8" in result.output

    def test_update(self) -> None:
        """测试 test update."""
        s = _make_mock_scheduler()
        s.schedule_config_operation = AsyncMock(return_value={"success": True})
        with (
            patch("sdpj.ui.cli.main._bootstrap", return_value=s),
            patch.object(CLIContext, "require_login", return_value=1),
        ):
            result = CliRunner().invoke(
                cli,
                [
                    "Config",
                    "update",
                    "--config-id",
                    "1",
                    "--model",
                    "deepseek-v4-pro",
                    "--request-format",
                    "anthropic",
                    "--api-key",
                    "sk-95033b3c11914e7484298d3b736f2d95",
                    "--base-url",
                    "https://api.deepseek.com/anthropic",
                    "--timeout",
                    "60",
                    "--max-rps",
                    "5",
                    "--max-concurrency",
                    "10",
                ],
            )
        assert result.exit_code == 0


class TestPrivateResourceOps:
    """测试 TestPrivateResourceOps 类."""

    def test_upload_dataset(self) -> None:
        """测试 test upload dataset."""
        s = _make_mock_scheduler()
        s.schedule_private_resource_operation = AsyncMock(
            return_value={"success": True, "info": {"dataset_id": 20}}
        )
        runner = CliRunner()
        with runner.isolated_filesystem():
            import json

            with open("ds.jsonl", "w", encoding="utf-8") as f:
                f.write('{"subtype": "jailbreak", "poc": "test poc"}\n')
            with (
                patch("sdpj.ui.cli.main._bootstrap", return_value=s),
                patch.object(CLIContext, "require_login", return_value=1),
            ):
                result = runner.invoke(cli, ["Config", "upload-dataset", "ds.jsonl"])
            assert result.exit_code == 0

    def test_remove_dataset(self) -> None:
        """测试 test remove dataset."""
        s = _make_mock_scheduler()
        s.schedule_private_resource_operation = AsyncMock(return_value={"success": True})
        result = _invoke(["Config", "remove-dataset", "--dataset-id", "20", "--yes"], s)
        assert result.exit_code == 0


# ═══════════════════════════════════════════════════════════
# System 命令
# ═══════════════════════════════════════════════════════════


class TestSystemLogs:
    """测试 TestSystemLogs 类."""

    def test_logs_with_invalid_user_id(self) -> None:
        """测试 test logs with invalid user id."""
        s = _make_mock_scheduler()
        result = _invoke(["System", "logs", "--user-id", "abc"], s)
        assert result.exit_code == 0
        assert "必须为整数" in result.output

    def test_logs_with_valid_user_id(self) -> None:
        """测试 test logs with valid user id."""
        s = _make_mock_scheduler()
        s.query_logs.return_value = {"logs": [], "total": 0}
        result = _invoke(["System", "logs", "--user-id", "42"], s)
        assert result.exit_code == 0
        s.query_logs.assert_called_once()
        filters = s.query_logs.call_args[0][0]
        assert filters["user_id"] == 42
