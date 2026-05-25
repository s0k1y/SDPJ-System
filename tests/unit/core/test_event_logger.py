"""
EventLogger 单元测试
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from sdpj.core.event_logger import EventLogger
from sdpj.core.event_logger_interface import LogCategory, LogLevel


def _query(logger, **kwargs):
    """同步包装异步 query_logs"""
    result, _ = asyncio.run(logger.query_logs(**kwargs))
    return result


class TestOperationLogging:
    """测试操作日志记录"""

    def test_log_operation_success(self):
        """测试成功记录用户操作"""
        logger = EventLogger()
        log_id = logger.log_operation(
            user_id="user1",
            operation_type="start_detection",
            context={"model": "gpt-4", "dataset": "dataset1"},
        )

        assert log_id is not None
        assert isinstance(log_id, str)

        # 验证日志已记录
        logs = _query(logger, user_id="user1")
        assert len(logs) == 1
        assert logs[0].log_id == log_id
        assert logs[0].category == LogCategory.OPERATION

    def test_log_multiple_operations(self):
        """测试记录多个用户操作"""
        logger = EventLogger()
        log_ids = []

        for i in range(3):
            log_id = logger.log_operation(user_id=f"user{i}", operation_type="login", context={})
            log_ids.append(log_id)

        # 验证所有日志ID唯一
        assert len(log_ids) == len(set(log_ids))

        # 验证所有日志已记录
        logs = _query(logger, category=LogCategory.OPERATION)
        assert len(logs) == 3

    def test_log_operation_with_sensitive_info(self):
        """测试记录包含敏感信息的操作（已脱敏）"""
        logger = EventLogger()
        log_id = logger.log_operation(
            user_id="user1",
            operation_type="change_password",
            context={"password": "***"},  # 已脱敏
        )

        logs = _query(logger, user_id="user1")
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
            description="状态从 IDLE 转为 RUNNING",
        )

        assert log_id is not None

        logs = _query(logger, source_module="StateScheduler")
        assert len(logs) == 1
        assert logs[0].category == LogCategory.RUNTIME

    def test_log_task_progress(self):
        """测试记录检测任务进度"""
        logger = EventLogger()
        log_id = logger.log_runtime(
            source_module="SDPJDetector", event_type="task_progress", description="任务进度: 50%"
        )

        logs = _query(logger, source_module="SDPJDetector")
        assert len(logs) == 1
        assert "50%" in logs[0].description

    def test_log_llm_call_phase(self):
        """测试记录大模型调用阶段"""
        logger = EventLogger()
        log_id = logger.log_runtime(
            source_module="LLMService",
            event_type="call_phase",
            description="大模型调用阶段: 请求发送",
        )

        logs = _query(logger, source_module="LLMService")
        assert len(logs) == 1


class TestErrorLogging:
    """测试错误日志记录"""

    def test_log_error_success(self):
        """测试成功记录错误日志"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="LLMService", error_type="api_error", description="API 调用失败: 超时"
        )

        assert log_id is not None

        logs = _query(logger, category=LogCategory.ERROR)
        assert len(logs) == 1
        assert logs[0].level == LogLevel.ERROR

    def test_log_database_error(self):
        """测试记录数据库访问错误"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="UserDB", error_type="database_error", description="数据库连接失败"
        )

        logs = _query(logger, source_module="UserDB")
        assert len(logs) == 1

    def test_log_permission_error(self):
        """测试记录权限校验失败"""
        logger = EventLogger()
        log_id = logger.log_error(
            source_module="DACManager",
            error_type="permission_error",
            description="用户 user1 权限校验失败",
        )

        logs = _query(logger, source_module="DACManager")
        assert len(logs) == 1
        assert "user1" in logs[0].description


class TestLogQuery:
    """测试日志查询"""

    def test_query_by_category(self):
        """测试按日志类别查询"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})
        logger.log_runtime("StateScheduler", "state_change", "状态转移")
        logger.log_error("LLMService", "api_error", "API 错误")

        # 查询错误日志
        error_logs = _query(logger, category=LogCategory.ERROR)
        assert len(error_logs) == 1
        assert error_logs[0].category == LogCategory.ERROR

    def test_query_by_time_range(self):
        """测试按时间范围查询"""
        logger = EventLogger()
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        logger.log_operation("user1", "login", {}, timestamp=now)

        logs = _query(logger, time_start=past, time_end=future)
        assert len(logs) == 1

    def test_query_by_source_module(self):
        """测试按来源模块查询"""
        logger = EventLogger()
        logger.log_runtime("SDPJDetector", "event1", "描述1")
        logger.log_runtime("StateScheduler", "event2", "描述2")

        logs = _query(logger, source_module="SDPJDetector")
        assert len(logs) == 1
        assert logs[0].source_module == "SDPJDetector"

    def test_query_by_user_id(self):
        """测试按用户ID查询"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})
        logger.log_operation("user2", "logout", {})

        logs = _query(logger, user_id="user1")
        assert len(logs) == 1
        assert logs[0].user_id == "user1"

    def test_query_multiple_conditions(self):
        """测试多条件组合查询"""
        logger = EventLogger()
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        logger.log_operation("user1", "login", {}, timestamp=now)
        logger.log_operation("user2", "login", {}, timestamp=now)

        # 查询特定用户在过去1小时的操作日志
        logs = _query(logger, category=LogCategory.OPERATION, user_id="user1", time_start=past)
        assert len(logs) == 1
        assert logs[0].user_id == "user1"

    def test_query_no_results(self):
        """测试查询无结果"""
        logger = EventLogger()
        logger.log_operation("user1", "login", {})

        logs = _query(logger, user_id="nonexistent")
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
        logs = _query(logger)
        assert len(logs) == 0

        # 记录 ERROR 级别日志（应被记录）
        logger.log_error("module", "error", "错误")
        logs = _query(logger)
        assert len(logs) == 1

    def test_set_log_level_debug(self):
        """测试设置日志级别为 DEBUG"""
        logger = EventLogger()
        logger.set_log_level(LogLevel.DEBUG)

        # 所有级别的日志都应被记录
        logger.log_operation("user1", "login", {})
        logger.log_runtime("module", "event", "事件")
        logger.log_error("module", "error", "错误")

        logs = _query(logger)
        assert len(logs) == 3

    def test_log_level_filtering(self):
        """测试日志级别过滤"""
        logger = EventLogger()
        logger.set_log_level(LogLevel.WARN)

        # INFO 级别应被过滤
        logger.log_operation("user1", "login", {})
        logs = _query(logger)
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
        logs = _query(logger)
        assert len(logs) == 1

    def test_set_duplicate_output_target(self):
        """测试添加重复的输出目标"""
        logger = EventLogger()
        logger.set_output_target("console")
        logger.set_output_target("console")  # 重复添加

        # 验证不重复添加
        assert "console" in logger._output_targets
        assert len([t for t in logger._output_targets if t == "console"]) == 1


class TestTimestampSorting:
    """测试时间戳排序BUG修复：旧日志本地时间 vs 新日志UTC时间"""

    def test_sort_utc_aware_before_local_naive(self):
        """UTC-aware日志应排在naive(本地时间)日志之前(降序，最新在前)

        模拟BUG场景：旧日志用本地时间23:40(CST/UTC+8)，新日志用UTC时间21:06。
        实际UTC时间：旧日志=15:40 UTC，新日志=21:06 UTC。
        正确排序：新日志(21:06)应在旧日志(15:40)前面。
        """
        logger = EventLogger()

        local_naive_ts = datetime(2026, 5, 5, 23, 40, 0)
        utc_aware_ts = datetime(2026, 5, 5, 21, 6, 0, tzinfo=timezone.utc)

        logger.log_runtime("OldModule", "old_event", "旧日志(本地时间)", timestamp=local_naive_ts)
        logger.log_runtime("NewModule", "new_event", "新日志(UTC时间)", timestamp=utc_aware_ts)

        logs = _query(logger)
        assert len(logs) == 2

        assert logs[0].source_module == "NewModule"
        assert logs[1].source_module == "OldModule"

    def test_sort_mixed_timestamps_across_midnight(self):
        """跨午夜场景：本地时间01:00(CST) = UTC 17:00(前一天)"""
        logger = EventLogger()

        local_naive_ts = datetime(2026, 5, 6, 1, 0, 0)
        utc_aware_ts = datetime(2026, 5, 5, 22, 0, 0, tzinfo=timezone.utc)

        logger.log_runtime("LocalMod", "local_event", "本地时间日志", timestamp=local_naive_ts)
        logger.log_runtime("UtcMod", "utc_event", "UTC时间日志", timestamp=utc_aware_ts)

        logs = _query(logger)
        assert len(logs) == 2

        assert logs[0].source_module == "UtcMod"
        assert logs[1].source_module == "LocalMod"

    def test_sort_all_utc_aware(self):
        """全部UTC-aware时间戳排序应正确"""
        logger = EventLogger()

        ts1 = datetime(2026, 5, 5, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc)
        ts3 = datetime(2026, 5, 5, 14, 0, 0, tzinfo=timezone.utc)

        logger.log_runtime("Mod1", "event1", "日志1", timestamp=ts1)
        logger.log_runtime("Mod2", "event2", "日志2", timestamp=ts2)
        logger.log_runtime("Mod3", "event3", "日志3", timestamp=ts3)

        logs = _query(logger)
        assert len(logs) == 3
        assert logs[0].source_module == "Mod3"
        assert logs[1].source_module == "Mod2"
        assert logs[2].source_module == "Mod1"

    def test_sort_all_naive(self):
        """全部naive时间戳排序应正确(视为UTC)"""
        logger = EventLogger()

        ts1 = datetime(2026, 5, 5, 10, 0, 0)
        ts2 = datetime(2026, 5, 5, 12, 0, 0)
        ts3 = datetime(2026, 5, 5, 14, 0, 0)

        logger.log_runtime("Mod1", "event1", "日志1", timestamp=ts1)
        logger.log_runtime("Mod2", "event2", "日志2", timestamp=ts2)
        logger.log_runtime("Mod3", "event3", "日志3", timestamp=ts3)

        logs = _query(logger)
        assert len(logs) == 3
        assert logs[0].source_module == "Mod3"
        assert logs[1].source_module == "Mod2"
        assert logs[2].source_module == "Mod1"

    def test_save_to_db_preserves_utc_aware(self):
        """_save_to_db应保留UTC-aware时间戳（不剥离时区信息）"""
        from unittest.mock import AsyncMock, MagicMock
        from sdpj.core.event_logger_interface import LogEntry

        logger = EventLogger()
        mock_db = AsyncMock()
        logger._result_db = mock_db

        utc_aware_ts = datetime(2026, 5, 5, 21, 6, 0, tzinfo=timezone.utc)
        entry = LogEntry(
            log_id="test-id",
            category=LogCategory.RUNTIME,
            level=LogLevel.INFO,
            timestamp=utc_aware_ts,
            source_module="TestModule",
            user_id=None,
            event_type="test_event",
            description="test",
            context={},
        )

        asyncio.run(logger._save_to_db(entry))

        call_args = mock_db.save_log.call_args
        saved_ts = call_args.kwargs.get("timestamp") or call_args[1].get("timestamp")

        assert saved_ts.tzinfo == timezone.utc
        assert saved_ts.year == 2026
        assert saved_ts.month == 5
        assert saved_ts.day == 5
        assert saved_ts.hour == 21
        assert saved_ts.minute == 6

    def test_save_to_db_annotates_naive_as_utc(self):
        """_save_to_db应将naive时间戳标注为UTC时区"""
        from unittest.mock import AsyncMock
        from sdpj.core.event_logger_interface import LogEntry

        logger = EventLogger()
        mock_db = AsyncMock()
        logger._result_db = mock_db

        naive_ts = datetime(2026, 5, 5, 15, 40, 0)
        entry = LogEntry(
            log_id="test-id",
            category=LogCategory.RUNTIME,
            level=LogLevel.INFO,
            timestamp=naive_ts,
            source_module="TestModule",
            user_id=None,
            event_type="test_event",
            description="test",
            context={},
        )

        asyncio.run(logger._save_to_db(entry))

        call_args = mock_db.save_log.call_args
        saved_ts = call_args.kwargs.get("timestamp") or call_args[1].get("timestamp")

        assert saved_ts.tzinfo == timezone.utc
        assert saved_ts.replace(tzinfo=None) == naive_ts


class TestTimestampMigration:
    """测试时间戳迁移逻辑"""

    def test_normalize_aware_timestamp(self):
        """有时区信息的时间戳应转为UTC-naive"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        aware_ts = "2026-05-05 21:06:00.123456+00:00"
        local_offset = timedelta(hours=8)

        result = SessionManager._normalize_timestamp(aware_ts, local_offset)

        assert result is not None
        assert "+00:00" not in result
        assert result.startswith("2026-05-05 21:06")

    def test_normalize_naive_local_timestamp(self):
        """无时区信息的本地时间戳应减去偏移量转为UTC"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        naive_ts = "2026-05-05 23:40:00.123456"
        local_offset = timedelta(hours=8)

        result = SessionManager._normalize_timestamp(naive_ts, local_offset)

        assert result is not None
        assert result.startswith("2026-05-05 15:40")

    def test_normalize_z_suffix_timestamp(self):
        """Z后缀的时间戳应正确处理"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        z_ts = "2026-05-05T21:06:00.123456Z"
        local_offset = timedelta(hours=8)

        result = SessionManager._normalize_timestamp(z_ts, local_offset)

        assert result is not None
        assert result.startswith("2026-05-05 21:06")

    def test_normalize_datetime_object_aware(self):
        """datetime对象(aware)应正确归一化"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        aware_dt = datetime(2026, 5, 5, 21, 6, 0, tzinfo=timezone.utc)
        local_offset = timedelta(hours=8)

        result = SessionManager._normalize_timestamp(aware_dt, local_offset)

        assert result is not None
        assert result.startswith("2026-05-05 21:06")

    def test_normalize_datetime_object_naive(self):
        """datetime对象(naive)应减去偏移量"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        naive_dt = datetime(2026, 5, 5, 23, 40, 0)
        local_offset = timedelta(hours=8)

        result = SessionManager._normalize_timestamp(naive_dt, local_offset)

        assert result is not None
        assert result.startswith("2026-05-05 15:40")

    def test_normalize_invalid_timestamp_returns_none(self):
        """无效时间戳应返回None"""
        from sdpj.infrastructure.database.result_db.session import SessionManager
        from datetime import timedelta

        local_offset = timedelta(hours=8)

        assert SessionManager._normalize_timestamp("invalid", local_offset) is None
        assert SessionManager._normalize_timestamp(12345, local_offset) is None
