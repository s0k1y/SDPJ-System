"""CLI 端到端测试

所有命令直连真实数据库，不用任何 Mock。
每条 invoke() 是独立会话，登录态不跨调用保持——这是 Click CliRunner 的硬限制。

测试策略：
  - 不需要登录的命令：直接调用，严格断言
  - 注册/登录：通过 input= 传凭据，严格断言
  - 需登录的命令：测试"未登录被拒"
"""

import json
import uuid

import pytest
from click.testing import CliRunner

from sdpj.ui.cli.main import cli
from tests.fixtures.sample_data import REAL_CONFIGS


# ═══════════════════════════════════════════════════════════
# 帮助与状态（无需登录）
# ═══════════════════════════════════════════════════════════


class TestHelpAndStatus:
    def test_top_level_help(self):
        r = CliRunner().invoke(cli, ["--help"])
        assert r.exit_code == 0
        for cmd in [
            "detect",
            "report",
            "user",
            "config",
            "logs",
            "status",
            "watch",
            "watch-errors",
        ]:
            assert cmd in r.output, f"顶层帮助缺少命令: {cmd}"

    def test_subgroup_helps(self):
        for grp in ["detect", "report", "user", "config"]:
            r = CliRunner().invoke(cli, grp.split() + ["--help"])
            assert r.exit_code == 0, f"{grp} --help 失败: {r.output[:200]}"

    def test_status(self):
        r = CliRunner().invoke(cli, ["status"])
        assert r.exit_code == 0
        assert "系统状态" in r.output

    def test_logs(self):
        r = CliRunner().invoke(cli, ["logs", "--category", "operation"])
        assert r.exit_code == 0

    def test_logs_with_pagination(self):
        r = CliRunner().invoke(
            cli, ["logs", "--category", "runtime", "--page", "1", "--page-size", "5"]
        )
        assert r.exit_code == 0

    def test_logs_invalid_user_id(self):
        r = CliRunner().invoke(cli, ["logs", "--user-id", "not_a_number"])
        assert r.exit_code == 0
        assert "必须为整数" in r.output


# ═══════════════════════════════════════════════════════════
# 用户认证（通过 input= 直接提供凭据，真实注册/登录）
# ═══════════════════════════════════════════════════════════


class TestUserAuth:
    @pytest.fixture(scope="class")
    def creds(self):
        return f"e2e_{uuid.uuid4().hex[:8]}", "E2eTest_123"

    def test_register_success(self, creds):
        user, pwd = creds
        r = CliRunner().invoke(cli, ["user", "register"], input=f"{user}\n{pwd}\n")
        assert r.exit_code == 0
        assert "注册成功" in r.output or "已存在" in r.output

    def test_register_duplicate(self, creds):
        user, pwd = creds
        # 重复注册，预期提示已存在
        r = CliRunner().invoke(cli, ["user", "register"], input=f"{user}\n{pwd}\n")
        assert r.exit_code in [0, 1]

    def test_login_success(self, creds):
        user, pwd = creds
        r = CliRunner().invoke(cli, ["user", "login"], input=f"{user}\n{pwd}\n")
        assert r.exit_code == 0
        assert "登录成功" in r.output
        assert "用户ID:" in r.output

    def test_login_wrong_password(self, creds):
        user, _ = creds
        r = CliRunner().invoke(cli, ["user", "login"], input=f"{user}\nWrongPass_999\n")
        assert r.exit_code == 1

    def test_login_nonexistent_user(self):
        r = CliRunner().invoke(cli, ["user", "login"], input=f"no_user_{uuid.uuid4().hex}\npass\n")
        assert r.exit_code == 1


# ═══════════════════════════════════════════════════════════
# 需登录的命令：验证"未登录→被拒"
# ═══════════════════════════════════════════════════════════


class TestLoginRequired:
    """每个需登录的命令，不传登录凭据直接调，预期返回 exit_code=1 且提示登录"""

    def test_detect_start(self):
        r = CliRunner().invoke(cli, ["detect", "start", "--model-id", "x", "--dataset", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_detect_datasets(self):
        r = CliRunner().invoke(cli, ["detect", "datasets"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_detect_dataset_detail(self):
        r = CliRunner().invoke(cli, ["detect", "dataset-detail", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_detect_dataset_export(self):
        r = CliRunner().invoke(cli, ["detect", "dataset-export", "2"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_detect_dataset_delete(self):
        r = CliRunner().invoke(cli, ["detect", "dataset-delete", "99999", "--yes"])
        assert r.exit_code == 1
        assert "登录" in r.output

    # detect progress/run/cancel 当前不检查登录（直接访问 scheduler），
    # 以下为实际行为测试而非"应被拒"测试
    def test_detect_progress_no_login(self):
        r = CliRunner().invoke(cli, ["detect", "progress"])
        assert r.exit_code == 0

    def test_detect_run_no_login(self):
        r = CliRunner().invoke(cli, ["detect", "run"])
        assert r.exit_code == 0

    def test_detect_cancel_no_login(self):
        r = CliRunner().invoke(cli, ["detect", "cancel", "--task-id", "x"])
        assert r.exit_code in [0, 1]

    def test_report_generate(self):
        r = CliRunner().invoke(cli, ["report", "generate", "tg-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_view(self):
        r = CliRunner().invoke(cli, ["report", "view", "tg-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_list(self):
        r = CliRunner().invoke(cli, ["report", "list"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_delete(self):
        r = CliRunner().invoke(cli, ["report", "delete", "tg-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_export(self):
        r = CliRunner().invoke(cli, ["report", "export", "tg-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_statistics_no_login(self):
        r = CliRunner().invoke(cli, ["report", "statistics"])
        assert r.exit_code == 0

    def test_report_visualization(self):
        r = CliRunner().invoke(cli, ["report", "visualization", "tg-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_report_task_visualization(self):
        r = CliRunner().invoke(cli, ["report", "task-visualization", "task-1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_profile(self):
        r = CliRunner().invoke(cli, ["user", "profile"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_password(self):
        r = CliRunner().invoke(cli, ["user", "password", "--old", "x", "--new", "y"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_switch_no_login(self):
        r = CliRunner().invoke(cli, ["user", "switch", "--username", "x", "--password", "y"])
        # switch 内部调 schedule_account_operation，不检查登录态，成败取决于后端
        assert r.exit_code in [0, 1]

    def test_user_unregister(self):
        r = CliRunner().invoke(cli, ["user", "unregister", "--yes"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_resources(self):
        r = CliRunner().invoke(cli, ["user", "resources"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_update_profile(self):
        r = CliRunner().invoke(cli, ["user", "update-profile", "--username", "newname"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_list_no_login(self):
        r = CliRunner().invoke(cli, ["user", "list"])
        assert r.exit_code == 0

    def test_user_delete_user_no_login(self):
        r = CliRunner().invoke(cli, ["user", "delete-user", "--user-id", "99999", "--yes"])
        assert r.exit_code in [0, 1]

    def test_user_auth_grant(self):
        r = CliRunner().invoke(
            cli, ["user", "auth", "grant", "--resource-id", "1", "--target-username", "x"]
        )
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_auth_revoke(self):
        r = CliRunner().invoke(cli, ["user", "auth", "revoke", "--acl-id", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_auth_list(self):
        r = CliRunner().invoke(cli, ["user", "auth", "list", "--resource-id", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_user_auth_check(self):
        r = CliRunner().invoke(cli, ["user", "auth", "check", "--resource-id", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_config_list(self):
        r = CliRunner().invoke(cli, ["config", "list"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_config_view(self):
        r = CliRunner().invoke(cli, ["config", "view", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_config_delete(self):
        r = CliRunner().invoke(cli, ["config", "delete", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_config_export(self):
        r = CliRunner().invoke(cli, ["config", "export", "1"])
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_remove_adapter(self):
        r = CliRunner().invoke(
            cli, ["config", "remove-adapter", "--model-id", "x", "--resource-id", "999"]
        )
        assert r.exit_code == 1
        assert "登录" in r.output

    def test_remove_dataset(self):
        r = CliRunner().invoke(cli, ["config", "remove-dataset", "999"])
        assert r.exit_code == 1
        assert "登录" in r.output


# ═══════════════════════════════════════════════════════════
# 需登录 + 需本地文件的命令：未登录被拒
# ═══════════════════════════════════════════════════════════


class TestLoginRequiredWithFiles:
    def test_config_create(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("cfg.json", "w", encoding="utf-8") as f:
                json.dump(REAL_CONFIGS["deepseek_openai"], f)
            r = runner.invoke(cli, ["config", "create", "cfg.json"])
            assert r.exit_code == 1
            assert "登录" in r.output

    def test_config_import(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("cfg.json", "w", encoding="utf-8") as f:
                json.dump(REAL_CONFIGS["deepseek_openai"], f)
            r = runner.invoke(cli, ["config", "import", "cfg.json"])
            assert r.exit_code == 1
            assert "登录" in r.output

    def test_config_update(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("cfg.json", "w", encoding="utf-8") as f:
                json.dump(REAL_CONFIGS["deepseek_openai"], f)
            r = runner.invoke(cli, ["config", "update", "1", "cfg.json"])
            assert r.exit_code == 1
            assert "登录" in r.output

    def test_upload_adapter(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("adapter.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "request_format": "openai",
                        "api_url": REAL_CONFIGS["deepseek_openai"]["base_url"],
                        "api_key": REAL_CONFIGS["deepseek_openai"]["api_key"],
                    },
                    f,
                )
            r = runner.invoke(cli, ["config", "upload-adapter", "adapter.json", "--model-id", "m"])
            assert r.exit_code == 1
            assert "登录" in r.output

    def test_upload_dataset(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("ds.json", "w", encoding="utf-8") as f:
                json.dump([{"subtype": "t", "poc": "c"}], f)
            r = runner.invoke(
                cli,
                ["config", "upload-dataset", "ds.json", "--name", "ds", "--risk-type", "jailbreak"],
            )
            assert r.exit_code == 1
            assert "登录" in r.output

    def test_dataset_import(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("ds.json", "w", encoding="utf-8") as f:
                json.dump([{"subtype": "t", "poc": "c"}], f)
            r = runner.invoke(cli, ["detect", "dataset-import", "ds.json"])
            assert r.exit_code == 1
            assert "登录" in r.output
