"""EventLogger 接口定义.

该模块定义了事件与日志管理的接口契约.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime


class LogLevel(Enum):
    """日志级别枚举."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogCategory(Enum):
    """日志类别枚举."""

    OPERATION = "operation"  # 操作日志
    RUNTIME = "runtime"  # 运行日志
    ERROR = "error"  # 错误日志


@dataclass
class LogEntry:
    """日志条目数据类."""

    log_id: str  # 日志条目标识
    category: LogCategory  # 日志类别
    level: LogLevel  # 日志级别
    timestamp: datetime  # 时间戳
    source_module: str  # 事件来源模块
    user_id: str | None  # 操作者用户ID(操作日志专用)
    event_type: str  # 事件类型/操作类型/错误类型
    description: str  # 事件描述/错误描述
    context: dict  # 操作上下文/关键参数


class EventLoggerInterface(Protocol):
    """事件与日志管理接口.

    该接口定义了日志记录和查询的核心能力,被 StateScheduler 调用.
    """

    def log_operation(
        self, user_id: str, operation_type: str, context: dict, timestamp: datetime | None = None,
    ) -> str:
        """记录用户操作日志.

        Args:
            user_id: 操作者用户ID
            operation_type: 操作类型
            context: 操作上下文(操作对象,关键参数等)
            timestamp: 时间戳(可选,默认为当前时间)

        Returns:
            日志条目标识

        """
        ...

    def log_runtime(
        self,
        source_module: str,
        event_type: str,
        description: str,
        timestamp: datetime | None = None,
    ) -> str:
        """记录系统运行日志.

        Args:
            source_module: 事件来源模块
            event_type: 事件类型
            description: 事件描述
            timestamp: 时间戳(可选,默认为当前时间)

        Returns:
            日志条目标识

        """
        ...

    def log_error(
        self,
        source_module: str,
        error_type: str,
        description: str,
        timestamp: datetime | None = None,
    ) -> str:
        """记录系统错误日志.

        Args:
            source_module: 错误来源模块
            error_type: 错误类型
            description: 错误描述
            timestamp: 时间戳(可选,默认为当前时间)

        Returns:
            日志条目标识

        """
        ...

    async def query_logs(  # noqa: PLR0913
        self,
        category: LogCategory | None = None,
        level: LogLevel | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        source_module: str | None = None,
        user_id: str | None = None,
        user_ids: list[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> tuple[list[LogEntry], int]:
        """按条件查询日志.

        Args:
            category: 日志类别(可选)
            level: 日志级别(可选)
            time_start: 时间范围起始(可选)
            time_end: 时间范围结束(可选)
            source_module: 来源模块(可选)
            user_id: 用户ID(可选)
            user_ids: 用户ID列表(可选)
            page: 页码(可选)
            page_size: 每页数量(可选)

        Returns:
            (匹配条件的日志条目列表, 总数)

        """
        ...

    def set_log_level(self, level: LogLevel) -> bool:
        """设置当前生效的日志级别.

        Args:
            level: 目标日志级别

        Returns:
            设置成功返回 True

        """
        ...

    def set_output_target(self, target: str) -> bool:
        """设置日志输出目标.

        Args:
            target: 目标输出通道("console" / "memory" / "stream")

        Returns:
            设置成功返回 True

        """
        ...

    def subscribe_logs(self, callback: Callable[[dict], None]) -> None:
        """订阅日志推送,callback 接收日志字典."""
        ...

    def unsubscribe_logs(self, callback: Callable[[dict], None]) -> None:
        """取消日志订阅."""
        ...

    async def start_db_writer(self) -> None:
        """启动异步数据库写入循环."""
        ...

    async def cleanup_old_logs(self, max_age_days: int = 7) -> int:
        """删除超过 max_age_days 天的旧日志,返回删除条数."""
        ...

    async def flush(self) -> None:
        """等待内存日志队列排空并取消数据库写入任务."""
        ...
