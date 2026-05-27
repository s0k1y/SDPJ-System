import json  # noqa: D100
import uuid

import pytest
from click.testing import CliRunner

from sdpj.ui.cli.main import cli
from sdpj.ui.cli.session import clear_session
from tests.fixtures.sample_data import REAL_CONFIGS


# ============================================================


class TestHelpAndStatus:  # noqa: D101
    def test_top_level_help(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["--help"])
        assert r.exit_code == 0

    def test_subgroup_helps(self) -> None:  # noqa: D102
        for grp in ["Detect", "Report", "User", "Config", "System"]:
            r = CliRunner().invoke(cli, [grp, "--help"])
            assert r.exit_code == 0, f"{grp} --help exit_code={r.exit_code}"

    def test_logs(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["System", "logs", "--category", "operation"])
        assert r.exit_code == 0

    def test_logs_with_pagination(self) -> None:  # noqa: D102
        r = CliRunner().invoke(
            cli, ["System", "logs", "--category", "runtime", "--page", "1", "--page-size", "5"]
        )
        assert r.exit_code == 0

    def test_logs_invalid_user_id(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["System", "logs", "--user-id", "not_a_number"])
        assert r.exit_code == 0


# ============================================================


class TestUserAuth:  # noqa: D101
    @pytest.fixture(scope="class")
    def creds(self):  # noqa: ANN201, D102
        return f"e2e_{uuid.uuid4().hex[:8]}", "E2eTest_123"

    def test_register_success(self, creds) -> None:  # noqa: ANN001, D102
        user, pwd = creds
        r = CliRunner().invoke(cli, ["User", "register"], input=f"{user}\n{pwd}\n")
        assert r.exit_code == 0

    def test_register_duplicate(self, creds) -> None:  # noqa: ANN001, D102
        user, pwd = creds
        r = CliRunner().invoke(cli, ["User", "register"], input=f"{user}\n{pwd}\n")
        assert r.exit_code in [0, 1]

    def test_login_success(self, creds) -> None:  # noqa: ANN001, D102
        user, pwd = creds
        r = CliRunner().invoke(cli, ["User", "login"], input=f"{user}\n{pwd}\n")
        assert r.exit_code == 0

    def test_login_wrong_password(self, creds) -> None:  # noqa: ANN001, D102
        user, _ = creds
        r = CliRunner().invoke(cli, ["User", "login"], input=f"{user}\nWrongPass_999\n")
        assert r.exit_code == 1

    def test_login_nonexistent_user(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "login"], input=f"no_user_{uuid.uuid4().hex}\npass\n")
        assert r.exit_code == 1


# ============================================================


class TestLoginRequired:
    """\u672a\u767b\u5f55\u2192exit_code=1\uff08ClickException\uff09"""

    @pytest.fixture(autouse=True)
    def _clear_session(self) -> None:
        clear_session()

    def test_detect_start(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, [
            "Detect", "task", "start",
            "--model-id", "x", "--type", "static", "--dataset", "1", "--config-id", "1",
        ])
        assert r.exit_code == 1

    def test_detect_progress(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Detect", "task", "progress"])
        assert r.exit_code == 0

    def test_detect_cancel(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Detect", "task", "cancel", "--task-id", "x"])
        assert r.exit_code in [0, 1]

    def test_report_view(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Report", "view", "--group-id", "tg-1"])
        assert r.exit_code == 1

    def test_report_list(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Report", "list"])
        assert r.exit_code == 1

    def test_report_delete(self) -> None:  # noqa: D102
        r = CliRunner().invoke(
            cli, ["Report", "delete", "--target-id", "tg-1", "--granularity", "task_group"]
        )
        assert r.exit_code == 1

    def test_report_export(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Report", "export", "--group-id", "tg-1"])
        assert r.exit_code == 1

    def test_report_statistics(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Report", "statistics"])
        assert r.exit_code == 0

    def test_report_visualization(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Report", "visualization", "--group-id", "tg-1"])
        assert r.exit_code == 1

    def test_user_profile(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "profile"])
        assert r.exit_code == 1

    def test_user_password(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "password", "--old", "x", "--new", "y"])
        assert r.exit_code == 1

    def test_user_switch(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "switch", "--username", "x", "--password", "y"])
        assert r.exit_code in [0, 1]

    def test_user_unregister(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "unregister", "--yes"])
        assert r.exit_code == 1

    def test_user_resources(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "resources"])
        assert r.exit_code == 1

    def test_user_list(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "list"])
        assert r.exit_code == 0

    def test_user_delete_user(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "delete-user", "--user-id", "99999", "--yes"])
        assert r.exit_code in [0, 1]

    def test_user_auth_grant(self) -> None:  # noqa: D102
        r = CliRunner().invoke(
            cli, ["User", "auth", "grant", "--resource-id", "1", "--target-username", "x"]
        )
        assert r.exit_code == 1

    def test_user_auth_revoke(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "auth", "revoke", "--acl-id", "1"])
        assert r.exit_code == 1

    def test_user_auth_show(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "auth", "show", "--resource-id", "1"])
        assert r.exit_code == 1

    def test_user_auth_check(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["User", "auth", "check", "--resource-id", "1"])
        assert r.exit_code == 1

    def test_config_list(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "list"])
        assert r.exit_code == 1

    def test_config_view(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "view", "--config-id", "1"])
        assert r.exit_code == 1

    def test_config_delete(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "delete", "--config-id", "1"])
        assert r.exit_code == 1

    def test_config_export(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "export", "--config-id", "1"])
        assert r.exit_code == 1

    def test_config_dataset_list(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "dataset", "list"])
        assert r.exit_code == 1

    def test_config_dataset_detail(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "dataset", "detail", "--id", "1"])
        assert r.exit_code == 1

    def test_config_export_dataset(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "export-dataset", "--id", "1"])
        assert r.exit_code == 1

    def test_config_remove_dataset(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, ["Config", "remove-dataset", "--dataset-id", "999"])
        assert r.exit_code == 1


# ============================================================


class TestLoginRequiredWithFiles:  # noqa: D101

    @pytest.fixture(autouse=True)
    def _clear_session(self) -> None:
        clear_session()

    def test_config_create(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, [
            "Config", "create",
            "--model", "m", "--request-format", "openai", "--api-key", "k",
            "--base-url", "http://x", "--timeout", "30",
            "--max-rps", "1", "--max-concurrency", "1",
        ])
        assert r.exit_code == 1

    def test_config_import(self) -> None:  # noqa: D102
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("cfg.json", "w", encoding="utf-8") as f:
                json.dump(REAL_CONFIGS["deepseek_openai"], f)
            r = runner.invoke(cli, ["Config", "import", "cfg.json"])
            assert r.exit_code == 1

    def test_config_update(self) -> None:  # noqa: D102
        r = CliRunner().invoke(cli, [
            "Config", "update", "--config-id", "1",
            "--model", "m", "--request-format", "openai", "--api-key", "k",
            "--base-url", "http://x", "--timeout", "30",
            "--max-rps", "1", "--max-concurrency", "1",
        ])
        assert r.exit_code == 1

    def test_upload_dataset(self) -> None:  # noqa: D102
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("ds.json", "w", encoding="utf-8") as f:
                json.dump([{"subtype": "t", "poc": "c"}], f)
            r = runner.invoke(cli, ["Config", "upload-dataset", "ds.json"])
            assert r.exit_code == 1
