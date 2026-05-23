"""
EventLogger 实现

该模块实现了事件与日志管理的核心功能。
"""

import asyncio
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import structlog

from .event_logger_interface import (
    EventLoggerInterface,
    LogCategory,
    LogEntry,
    LogLevel,
)

_MAX_MEMORY_LOGS = 10000


class EventLogger(EventLoggerInterface):
    """
    事件与日志管理器

    负责记录和管理系统运行期的所有关键事件。
    使用 structlog 实现结构化日志，支持内存和数据库双重存储。
    """

    # 日志级别优先级映射
    _LEVEL_PRIORITY = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARN: 2,
        LogLevel.ERROR: 3,
    }

    def __init__(self, result_db=None, output_targets: set[str] | None = None):
        """初始化事件与日志管理器

        Args:
            result_db: ResultDB 实例，用于持久化日志
            output_targets: 输出目标集合，默认 {"memory", "database"}，可加 "console"
        """
        self._logs: deque[LogEntry] = deque(maxlen=_MAX_MEMORY_LOGS)
        self._current_level: LogLevel = LogLevel.INFO
        self._output_targets: set[str] = output_targets or {"memory", "database"}
        self._result_db = result_db
        self._log_subscribers: list[Callable[[dict], None]] = []
        self._log_queue: asyncio.Queue | None = None
        self._db_writer_task: asyncio.Task | None = None

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

    @staticmethod
    def _ensure_utc(ts: datetime) -> datetime:
        """确保时间戳为UTC-aware格式

        naive datetime视为本地时间，转换为UTC-aware。
        aware datetime保持不变。
        """
        if ts.tzinfo is None:
            local_offset = datetime.now().astimezone().utcoffset()
            if local_offset:
                ts = (ts - local_offset).replace(tzinfo=timezone.utc)
            else:
                ts = ts.replace(tzinfo=timezone.utc)
        return ts

    def log_operation(
        self, user_id: str, operation_type: str, context: dict, timestamp: datetime | None = None
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
        ts = self._ensure_utc(timestamp or datetime.now(timezone.utc))

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.OPERATION,
            level=LogLevel.INFO,
            timestamp=ts,
            source_module="user",
            user_id=user_id,
            event_type=operation_type,
            description=operation_type,
            context=context,
        )

        self._add_log(entry)
        return log_id

    def log_runtime(
        self,
        source_module: str,
        event_type: str,
        description: str,
        timestamp: datetime | None = None,
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
        ts = self._ensure_utc(timestamp or datetime.now(timezone.utc))

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.RUNTIME,
            level=LogLevel.INFO,
            timestamp=ts,
            source_module=source_module,
            user_id=None,
            event_type=event_type,
            description=description,
            context={},
        )

        self._add_log(entry)
        return log_id

    def log_error(
        self,
        source_module: str,
        error_type: str,
        description: str,
        timestamp: datetime | None = None,
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
        ts = self._ensure_utc(timestamp or datetime.now(timezone.utc))

        entry = LogEntry(
            log_id=log_id,
            category=LogCategory.ERROR,
            level=LogLevel.ERROR,
            timestamp=ts,
            source_module=source_module,
            user_id=None,
            event_type=error_type,
            description=description,
            context={},
        )

        self._add_log(entry)
        return log_id

    def _filter_entry(
        self,
        entry: LogEntry,
        category: LogCategory | None = None,
        level: LogLevel | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        source_module: str | None = None,
        user_id: str | None = None,
        user_ids: list[str] | None = None,
    ) -> bool:
        if category is not None and entry.category != category:
            return False
        if level is not None and entry.level != level:
            return False
        if time_start is not None and entry.timestamp < time_start:
            return False
        if time_end is not None and entry.timestamp > time_end:
            return False
        if source_module is not None and entry.source_module != source_module:
            return False
        if user_id is not None and entry.user_id != user_id:
            return False
        if user_ids is not None and entry.user_id not in user_ids:
            return False
        return True

    async def query_logs(
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
        """
        按条件查询日志

        同时查询内存和数据库，合并去重后返回。
        支持分页查询，当 page 和 page_size 均不为 None 时启用分页。

        Args:
            category: 日志类别
            level: 日志级别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID
            user_ids: 用户ID列表（IN查询）
            page: 页码（从1开始），为None时不分页
            page_size: 每页数量，为None时不分页

        Returns:
            (日志条目列表, 总数)
        """
        ts_start = self._ensure_utc(time_start) if time_start is not None else None
        ts_end = self._ensure_utc(time_end) if time_end is not None else None

        memory_matches: list[LogEntry] = []
        for entry in self._logs:
            if not self._filter_entry(
                entry, category, level, ts_start, ts_end, source_module, user_id, user_ids
            ):
                continue
            memory_matches.append(entry)

        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            db_entries: list[LogEntry] = []
            db_total = 0

            if self._result_db is not None and "database" in self._output_targets:
                try:
                    db_entries = await self._query_from_db(
                        category,
                        level,
                        time_start,
                        time_end,
                        source_module,
                        user_id,
                        user_ids,
                        limit=page_size,
                        offset=offset,
                    )
                    db_total = await self._count_from_db(
                        category, level, time_start, time_end, source_module, user_id, user_ids
                    )
                except Exception as e:
                    self._logger.error(f"从数据库查询日志失败: {e}")

            db_ids = {e.log_id for e in db_entries}
            memory_only = [e for e in memory_matches if e.log_id not in db_ids]
            memory_only.sort(
                key=lambda e: (
                    e.timestamp.replace(tzinfo=timezone.utc)
                    if e.timestamp.tzinfo is None
                    else e.timestamp
                ),
                reverse=True,
            )

            total = db_total + len(memory_only)

            if page == 1:
                results = memory_only + db_entries
                results = results[:page_size]
            else:
                results = db_entries

            return results, total
        else:
            seen_ids: set[str] = set()
            results: list[LogEntry] = []

            for entry in memory_matches:
                seen_ids.add(entry.log_id)
                results.append(entry)

            if self._result_db is not None and "database" in self._output_targets:
                try:
                    db_entries = await self._query_from_db(
                        category, level, time_start, time_end, source_module, user_id, user_ids
                    )
                    for entry in db_entries:
                        if entry.log_id not in seen_ids:
                            seen_ids.add(entry.log_id)
                            results.append(entry)
                except Exception as e:
                    self._logger.error(f"从数据库查询日志失败: {e}")

            results.sort(
                key=lambda e: (
                    e.timestamp.replace(tzinfo=timezone.utc)
                    if e.timestamp.tzinfo is None
                    else e.timestamp
                ),
                reverse=True,
            )
            return results, len(results)

    async def _query_from_db(
        self,
        category: LogCategory | None,
        level: LogLevel | None,
        time_start: datetime | None,
        time_end: datetime | None,
        source_module: str | None,
        user_id: str | None,
        user_ids: list[str] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[LogEntry]:
        """从数据库查询日志（异步）"""
        logs = await self._result_db.query_logs(
            category=category.value if category else None,
            level=level.value if level else None,
            time_start=time_start,
            time_end=time_end,
            source_module=source_module,
            user_id=user_id,
            user_ids=user_ids,
            limit=limit,
            offset=offset,
        )

        return [
            LogEntry(
                log_id=log["log_id"],
                category=LogCategory(log["category"]),
                level=LogLevel(log["level"]),
                timestamp=log["timestamp"],
                source_module=log["source_module"],
                user_id=log["user_id"],
                event_type=log["event_type"],
                description=log["description"],
                context=log["context"] or {},
            )
            for log in logs
        ]

    async def _count_from_db(
        self,
        category: LogCategory | None,
        level: LogLevel | None,
        time_start: datetime | None,
        time_end: datetime | None,
        source_module: str | None,
        user_id: str | None,
        user_ids: list[str] | None = None,
    ) -> int:
        """从数据库统计日志数量（异步）"""
        return await self._result_db.count_logs(
            category=category.value if category else None,
            level=level.value if level else None,
            time_start=time_start,
            time_end=time_end,
            source_module=source_module,
            user_id=user_id,
            user_ids=user_ids,
        )

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

    def subscribe_logs(self, callback: Callable[[dict], None]) -> None:
        if callback not in self._log_subscribers:
            self._log_subscribers.append(callback)

    def unsubscribe_logs(self, callback: Callable[[dict], None]) -> None:
        if callback in self._log_subscribers:
            self._log_subscribers.remove(callback)

    async def start_db_writer(self) -> None:
        if self._log_queue is None:
            self._log_queue = asyncio.Queue(maxsize=10000)
        if self._db_writer_task is None or self._db_writer_task.done():
            self._db_writer_task = asyncio.create_task(self._db_writer_loop())

    async def cleanup_old_logs(self, max_age_days: int = 7, cooldown_days: int = 1) -> int:
        """清理过期日志

        当距上次清理超过 cooldown_days 天时，删除超过 max_age_days 天的日志。

        Args:
            max_age_days: 日志保留天数
            cooldown_days: 清理冷却天数

        Returns:
            删除的日志数量
        """
        marker = Path("./sdpj/infrastructure/database/.last_log_cleanup")
        now = datetime.now(timezone.utc)

        if marker.exists():
            try:
                last_ts = datetime.fromisoformat(marker.read_text().strip())
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=timezone.utc)
                if now - last_ts < timedelta(days=cooldown_days):
                    return 0
            except (ValueError, OSError):
                pass

        if self._result_db is None:
            return 0

        cutoff = now - timedelta(days=max_age_days)
        try:
            deleted = await self._result_db.delete_old_logs(cutoff)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(now.isoformat())
            if deleted > 0:
                self._logger.info(f"已清理 {deleted} 条超过 {max_age_days} 天的日志")
            return deleted
        except Exception as e:
            self._logger.error(f"清理日志失败: {e}")
            return 0

    async def _db_writer_loop(self) -> None:
        while True:
            entry = await self._log_queue.get()
            try:
                await self._save_to_db(entry)
            except Exception as e:
                self._logger.error("log_db_write_failed", error=str(e), log_id=entry.log_id)
            finally:
                self._log_queue.task_done()

    async def flush(self) -> None:
        if self._log_queue is not None:
            await self._log_queue.join()
        if self._db_writer_task is not None and not self._db_writer_task.done():
            self._db_writer_task.cancel()
            try:
                await self._db_writer_task
            except asyncio.CancelledError:
                pass

    def _add_log(self, entry: LogEntry) -> None:
        if self._LEVEL_PRIORITY[entry.level] < self._LEVEL_PRIORITY[self._current_level]:
            return

        if "memory" in self._output_targets:
            self._logs.append(entry)

        if "database" in self._output_targets and self._result_db is not None:
            if self._log_queue is not None:
                try:
                    self._log_queue.put_nowait(entry)
                except asyncio.QueueFull:
                    self._logger.error("log_queue_full", log_id=entry.log_id)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._save_to_db(entry))
                except RuntimeError:
                    try:
                        asyncio.run(self._save_to_db(entry))
                    except Exception as e:
                        self._logger.error(f"保存日志到数据库失败: {e}")

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

        log_dict = {
            "log_id": entry.log_id,
            "category": entry.category.value,
            "level": entry.level.value,
            "timestamp": entry.timestamp.isoformat()
            if isinstance(entry.timestamp, datetime)
            else str(entry.timestamp),
            "source_module": entry.source_module,
            "user_id": entry.user_id,
            "event_type": entry.event_type,
            "description": entry.description,
            "context": entry.context,
        }
        for cb in list(self._log_subscribers):
            try:
                cb(log_dict)
            except Exception:
                pass

    async def _save_to_db(self, entry: LogEntry) -> None:
        try:
            ts = entry.timestamp
            if ts.tzinfo is not None:
                ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
            await self._result_db.save_log(
                log_id=entry.log_id,
                category=entry.category.value,
                level=entry.level.value,
                timestamp=ts,
                source_module=entry.source_module,
                user_id=entry.user_id,
                event_type=entry.event_type,
                description=entry.description,
                context=entry.context,
            )
        except Exception as e:
            self._logger.error("save_log_to_db_failed", error=str(e), log_id=entry.log_id)
