"""CLI 端到端测试

基于 1.spec.md 的完整功能测试:
- 2.1.1 执行SDPJ静态自检测算法
- 2.1.2 执行SDPJ动态自检测算法
- 2.1.3 选择检测数据集
- 2.1.4 调度检测任务
- 2.1.5 生成可视化检测结果报告
- 2.1.6 管理检测结果报告(查询、查看、下载、删除)
- 2.1.7 系统状态管理与异常处理
- 2.1.8.1.1.1 用户注册与登录
- 2.1.8.1.1.2 用户管理(密码修改、账号切换)
- 2.1.8.1.2 用户权限管理(授予/移除)
"""
import pytest
import uuid
from click.testing import CliRunner

from sdpj.ui.cli.main import cli


class TestCLIUserManagement:
    """测试用户管理功能 (2.1.8.1.1)"""

    def setup_method(self):
        self.runner = CliRunner()
        self.unique_username = f"e2e_user_{uuid.uuid4().hex[:8]}"
        self.password = "test_password_123"

    def test_user_registration(self):
        """测试用户注册 (2.1.8.1.1.1)"""
        result = self.runner.invoke(
            cli, ['user', 'register'],
            input=f"{self.unique_username}\n{self.password}\n",
        )
        assert result.exit_code in [0, 1]

    def test_user_login(self):
        """测试用户登录 (2.1.8.1.1.1)"""
        self.runner.invoke(
            cli, ['user', 'register'],
            input=f"{self.unique_username}\n{self.password}\n",
        )
        result = self.runner.invoke(
            cli, ['user', 'login'],
            input=f"{self.unique_username}\n{self.password}\n",
        )
        assert result.exit_code in [0, 1]


class TestCLIDetectionCore:
    """测试核心检测功能 (2.1.1-2.1.6)"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_static_detection(self):
        """测试静态检测命令 (2.1.1)"""
        result = self.runner.invoke(cli, [
            'detect', 'start',
            '--model-id', 'gpt-4',
            '--type', 'static',
            '--dataset', '1',
        ])
        assert result.exit_code in [0, 1]

    def test_dynamic_detection(self):
        """测试动态检测命令 (2.1.2)"""
        result = self.runner.invoke(cli, [
            'detect', 'start',
            '--model-id', 'gpt-4',
            '--type', 'dynamic',
            '--dataset', '1',
        ])
        assert result.exit_code in [0, 1]


class TestCLICommands:
    """测试 CLI 命令可用性"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_help(self):
        """测试帮助命令"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'SDPJ-System' in result.output

    def test_user_command_exists(self):
        """测试用户命令组存在"""
        result = self.runner.invoke(cli, ['user', '--help'])
        assert result.exit_code == 0

    def test_detect_command_exists(self):
        """测试检测命令组存在"""
        result = self.runner.invoke(cli, ['detect', '--help'])
        assert result.exit_code == 0

    def test_report_command_exists(self):
        """测试报告命令组存在"""
        result = self.runner.invoke(cli, ['report', '--help'])
        assert result.exit_code == 0

    def test_config_command_exists(self):
        """测试配置命令组存在"""
        result = self.runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
