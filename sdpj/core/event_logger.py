"""
EventLogger 实现

该模块实现了事件与日志管理的核心功能。
"""
import uuid
from datetime import datetime
from typing import List

import structlog

from .event_logger_interface import (
    EventLoggerInterface,
    LogCategory,
    LogEntry,
    LogLevel,
)


class EventLogger(EventLoggerInterface):
    """
    事件与日志管理器

    负责记录和管理系统运行期的所有关键事件。
    使用 structlog 实现结构化日志，内存存储日志条目。
    """

    # 日志级别优先级映射
    _LEVEL_PRIORITY = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARN: 2,
        LogLevel.ERROR: 3,
    }

    def __init__(self):
        """初始化事件与日志管理器"""
        self._logs: List[LogEntry] = []
        self._current_level: LogLevel = LogLevel.INFO
        self._output_targets: set[str] = {"memory"}

        # 配置 structlog（简化配置）
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=False,
        )
        self._logger = structlog.get_logger()

    def log_operation(
        self,
        user_id: str,
        operation_type: str,
        context: dict,
        timestamp: datetime | None = None
    ) -> str:
        """
        记录用户操作日志

        Args:
            user_id: 操作者用户ID
            operation_type: 操作类型
            context: 操作上下文
            timestamp: 时间戳

        Returns:
            日志条目标识
        """
        log_id = str(uuid.uuid4())
        ts = timestamp or datetime.now()

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.OPERATION,
            level=LogLevel.INFO,
            timestamp=ts,
            source_module="user",
            user_id=user_id,
            event_type=operation_type,
            description=f"用户操作: {operation_type}",
            context=context
        )

        self._add_log(entry)
        return log_id

    def log_runtime(
        self,
        source_module: str,
        event_type: str,
        description: str,
        timestamp: datetime | None = None
    ) -> str:
        """
        记录系统运行日志

        Args:
            source_module: 事件来源模块
            event_type: 事件类型
            description: 事件描述
            timestamp: 时间戳

        Returns:
            日志条目标识
        """
        log_id = str(uuid.uuid4())
        ts = timestamp or datetime.now()

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.RUNTIME,
            level=LogLevel.INFO,
            timestamp=ts,
            source_module=source_module,
            user_id=None,
            event_type=event_type,
            description=description,
            context={}
        )

        self._add_log(entry)
        return log_id

    def log_error(
        self,
        source_module: str,
        error_type: str,
        description: str,
        timestamp: datetime | None = None
    ) -> str:
        """
        记录系统错误日志

        Args:
            source_module: 错误来源模块
            error_type: 错误类型
            description: 错误描述
            timestamp: 时间戳

        Returns:
            日志条目标识
        """
        log_id = str(uuid.uuid4())
        ts = timestamp or datetime.now()

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.ERROR,
            level=LogLevel.ERROR,
            timestamp=ts,
            source_module=source_module,
            user_id=None,
            event_type=error_type,
            description=description,
            context={}
        )

        self._add_log(entry)
        return log_id

    def query_logs(
        self,
        category: LogCategory | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        source_module: str | None = None,
        user_id: str | None = None
    ) -> list[LogEntry]:
        """
        按条件查询日志

        Args:
            category: 日志类别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID

        Returns:
            匹配条件的日志条目列表
        """
        results = []

        for entry in self._logs:
            # 按类别过滤
            if category is not None and entry.category != category:
                continue

            # 按时间范围过滤
            if time_start is not None and entry.timestamp < time_start:
                continue
            if time_end is not None and entry.timestamp > time_end:
                continue

            # 按来源模块过滤
            if source_module is not None and entry.source_module != source_module:
                continue

            # 按用户ID过滤
            if user_id is not None and entry.user_id != user_id:
                continue

            results.append(entry)

        return results

    def set_log_level(self, level: LogLevel) -> bool:
        """
        设置当前生效的日志级别

        Args:
            level: 目标日志级别

        Returns:
            设置成功返回 True
        """
        self._current_level = level
        return True

    def set_output_target(self, target: str) -> bool:
        """
        设置日志输出目标

        Args:
            target: 目标输出通道

        Returns:
            设置成功返回 True
        """
        if target not in self._output_targets:
            self._output_targets.add(target)
        return True

    def _add_log(self, entry: LogEntry) -> None:
        """
        添加日志条目到存储

        Args:
            entry: 日志条目
        """
        # 日志级别过滤
        if self._LEVEL_PRIORITY[entry.level] < self._LEVEL_PRIORITY[self._current_level]:
            return

        # 添加到内存存储
        if "memory" in self._output_targets:
            self._logs.append(entry)

        # 输出到控制台
        if "console" in self._output_targets:
            self._logger.info(
                entry.description,
                log_id=entry.log_id,
                category=entry.category.value,
                level=entry.level.value,
                source_module=entry.source_module,
                user_id=entry.user_id,
                event_type=entry.event_type,
            )
