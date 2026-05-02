"""
EventLogger 单元测试
"""
from datetime import datetime, timedelta

import pytest

from sdpj.core.event_logger import EventLogger
from sdpj.core.event_logger_interface import LogCategory, LogLevel


class TestOperationLogging:
    """测试操作日志记录"""

    def test_log_operation_success(self):
        """测试成功记录用户操作"""
        logger = EventLogger()
        log_id = logger.log_operation(
            user_id="user1",
            operation_type="start_detection",
            context={"model": "gpt-4", "dataset": "dataset1"}
        )

        assert log_id is not None
        assert isinstance(log_id, str)

        # 验证日志已记录
        logs = logger.query_logs(user_id="user1")
        assert len(logs) == 1
        assert logs[0].log_id == log_id
        assert logs[0].category == LogCategory.OPERATION

    def test_log_multiple_operations(self):
        """测试记录多个用户操作"""
        logger = EventLogger()
        log_ids = []

        for i in range(3):
            log_id = logger.log_operation(
                user_id=f"user{i}",
                operation_type="login",
                context={}
            )
            log_ids.append(log_id)

        # 验证所有日志ID唯一
        assert len(log_ids) == len(set(log_ids))

        # 验证所有日志已记录
        logs = logger.query_logs(category=LogCategory.OPERATION)
        assert len(logs) == 3

    def test_log_operation_with_sensitive_info(self):
        """测试记录包含敏感信息的操作（已脱敏）"""
        logger = EventLogger()
        log_id = logger.log_operation(
            user_id="user1",
            operation_type="change_password",
            context={"password": "***"}  # 已脱敏
        )

        logs = logger.query_logs(user_id="user1")
        # 验证直接记录，不做额外脱敏
        assert len(logs) == 1
        assert logs[0].context["password"] == "***"


class TestRuntimeLogging:
    """测试运行日志记录"""

    def test_log_runtime_success(self):
        """测试成功记录系统运行事件"""
        logger = EventLogger()
        log_id = logger.log_runtime(
            source_module="StateScheduler",
            event_type="state_transition",
            description="状态从 IDLE 转为 RUNNING"
        )

        assert log_id is not None

        logs = logger.query_logs(source_module="StateScheduler")
        assert len(logs) == 1
        assert logs[0].category == LogCategory.RUNTIME

    def test_log_task_progress(self):
        """测试记录检测任务进度"""
        logger = EventLogger()
        log_id = logger.log_runtime(
            source_module="SDPJDetector",
            event_type="task_progress",
            description="任务进度: 50%"
        )

        logs = logger.query_logs(source_module="SDPJDetector")
        assert len(logs) == 1
        assert "50%" in logs[0].description

    def test_log_llm_call_phase(self):
        """测试记录大模型调用阶段"""
        logger = EventLogger()
        log_id = logger.log_runtime(
            source_module="LLMInterface",
            event_type="call_phase",
            description="大模型调用阶段: 请求发送"
        )

        logs = logger.query_logs(source_module="LLMInterface")
        assert len(logs) == 1


class TestErrorLogging:
    """测试错误日志记录"""

    def test_log_error_success(self):
        """测试成功记录错误日志"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="LLMInterface",
            error_type="api_error",
            description="API 调用失败: 超时"
        )

        assert log_id is not None

        logs = logger.query_logs(category=LogCategory.ERROR)
        assert len(logs) == 1
        assert logs[0].level == LogLevel.ERROR

    def test_log_database_error(self):
        """测试记录数据库访问错误"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="UserDB",
            error_type="database_error",
            description="数据库连接失败"
        )

        logs = logger.query_logs(source_module="UserDB")
        assert len(logs) == 1

    def test_log_permission_error(self):
        """测试记录权限校验失败"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="DACManager",
            error_type="permission_error",
            description="用户 user1 权限校验失败"
        )

        logs = logger.query_logs(source_module="DACManager")
        assert len(logs) == 1
        assert "user1" in logs[0].description


class TestLogQuery:
    """测试日志查询"""

    def test_query_by_category(self):
        """测试按日志类别查询"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})
        logger.log_runtime("StateScheduler", "state_change", "状态转移")
        logger.log_error("LLMInterface", "api_error", "API 错误")

        # 查询错误日志
        error_logs = logger.query_logs(category=LogCategory.ERROR)
        assert len(error_logs) == 1
        assert error_logs[0].category == LogCategory.ERROR

    def test_query_by_time_range(self):
        """测试按时间范围查询"""
        logger = EventLogger()
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        logger.log_operation("user1", "login", {}, timestamp=now)

        # 查询过去1小时到未来1小时的日志
        logs = logger.query_logs(time_start=past, time_end=future)
        assert len(logs) == 1

    def test_query_by_source_module(self):
        """测试按来源模块查询"""
        logger = EventLogger()
        logger.log_runtime("SDPJDetector", "event1", "描述1")
        logger.log_runtime("StateScheduler", "event2", "描述2")

        logs = logger.query_logs(source_module="SDPJDetector")
        assert len(logs) == 1
        assert logs[0].source_module == "SDPJDetector"

    def test_query_by_user_id(self):
        """测试按用户ID查询"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})
        logger.log_operation("user2", "logout", {})

        logs = logger.query_logs(user_id="user1")
        assert len(logs) == 1
        assert logs[0].user_id == "user1"

    def test_query_multiple_conditions(self):
        """测试多条件组合查询"""
        logger = EventLogger()
        now = datetime.now()
        past = now - timedelta(hours=1)

        logger.log_operation("user1", "login", {}, timestamp=now)
        logger.log_operation("user2", "login", {}, timestamp=now)

        # 查询特定用户在过去1小时的操作日志
        logs = logger.query_logs(
            category=LogCategory.OPERATION,
            user_id="user1",
            time_start=past
        )
        assert len(logs) == 1
        assert logs[0].user_id == "user1"

    def test_query_no_results(self):
        """测试查询无结果"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})

        logs = logger.query_logs(user_id="nonexistent")
        assert len(logs) == 0


class TestLogLevelManagement:
    """测试日志级别管理"""

    def test_set_log_level_error(self):
        """测试设置日志级别为 ERROR"""
        logger = EventLogger()
        result = logger.set_log_level(LogLevel.ERROR)
        assert result is True

        # 记录 INFO 级别日志（应被过滤）
        logger.log_operation("user1", "login", {})
        logs = logger.query_logs()
        assert len(logs) == 0

        # 记录 ERROR 级别日志（应被记录）
        logger.log_error("module", "error", "错误")
        logs = logger.query_logs()
        assert len(logs) == 1

    def test_set_log_level_debug(self):
        """测试设置日志级别为 DEBUG"""
        logger = EventLogger()
        logger.set_log_level(LogLevel.DEBUG)

        # 所有级别的日志都应被记录
        logger.log_operation("user1", "login", {})
        logger.log_runtime("module", "event", "事件")
        logger.log_error("module", "error", "错误")

        logs = logger.query_logs()
        assert len(logs) == 3

    def test_log_level_filtering(self):
        """测试日志级别过滤"""
        logger = EventLogger()
        logger.set_log_level(LogLevel.WARN)

        # INFO 级别应被过滤
        logger.log_operation("user1", "login", {})
        logs = logger.query_logs()
        assert len(logs) == 0


class TestOutputTargetManagement:
    """测试输出目标管理"""

    def test_set_output_target_console(self):
        """测试设置输出到控制台"""
        logger = EventLogger()
        result = logger.set_output_target("console")
        assert result is True

    def test_set_output_target_memory(self):
        """测试设置输出到内存缓冲"""
        logger = EventLogger()
        result = logger.set_output_target("memory")
        assert result is True

    def test_set_multiple_output_targets(self):
        """测试设置多个输出目标"""
        logger = EventLogger()
        logger.set_output_target("console")
        logger.set_output_target("memory")

        # 验证日志同时输出到两个目标
        logger.log_operation("user1", "login", {})
        logs = logger.query_logs()
        assert len(logs) == 1

    def test_set_duplicate_output_target(self):
        """测试添加重复的输出目标"""
        logger = EventLogger()
        logger.set_output_target("console")
        logger.set_output_target("console")  # 重复添加

        # 验证不重复添加
        assert "console" in logger._output_targets
        assert len([t for t in logger._output_targets if t == "console"]) == 1
