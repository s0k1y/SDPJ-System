"""系统日志仓储层实现.

提供系统日志的 CRUD 操作.
"""

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.result_db.models import SystemLog


class LogRepository:
    """系统日志仓储.

    封装系统日志的数据访问逻辑.
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储.

        Args:
            session: 异步数据库会话

        """
        self.session = session

    async def create(  # noqa: PLR0913
        self,
        log_id: str,
        category: str,
        level: str,
        timestamp: datetime,
        source_module: str,
        user_id: str | None,
        event_type: str,
        description: str,
        context: dict | None,
    ) -> SystemLog:
        """创建日志记录.

        Args:
            log_id: 日志ID
            category: 日志类别
            level: 日志级别
            timestamp: 时间戳
            source_module: 来源模块
            user_id: 用户ID
            event_type: 事件类型
            description: 事件描述
            context: 上下文信息

        Returns:
            创建的日志对象

        """
        log = SystemLog(
            log_id=log_id,
            category=category,
            level=level,
            timestamp=timestamp,
            source_module=source_module,
            user_id=user_id,
            event_type=event_type,
            description=description,
            context=context,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def query(  # noqa: PLR0913
        self,
        category: str | None = None,
        level: str | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        source_module: str | None = None,
        user_id: str | None = None,
        user_ids: list[str] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[SystemLog]:
        """按条件查询日志.

        Args:
            category: 日志类别
            level: 日志级别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID
            user_ids: 用户ID列表(IN查询)
            limit: 返回结果数量限制
            offset: 偏移量

        Returns:
            匹配条件的日志列表

        """
        conditions = []

        if category is not None:
            conditions.append(SystemLog.category == category)
        if level is not None:
            conditions.append(SystemLog.level == level)
        if time_start is not None:
            conditions.append(SystemLog.timestamp >= time_start)
        if time_end is not None:
            conditions.append(SystemLog.timestamp <= time_end)
        if source_module is not None:
            conditions.append(SystemLog.source_module == source_module)
        if user_id is not None:
            conditions.append(SystemLog.user_id == user_id)
        if user_ids is not None:
            conditions.append(SystemLog.user_id.in_(user_ids))

        stmt = select(SystemLog)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(SystemLog.timestamp.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(  # noqa: PLR0913
        self,
        category: str | None = None,
        level: str | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        source_module: str | None = None,
        user_id: str | None = None,
        user_ids: list[str] | None = None,
    ) -> int:
        """按条件统计日志数量.

        Args:
            category: 日志类别
            level: 日志级别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID
            user_ids: 用户ID列表(IN查询)

        Returns:
            匹配条件的日志数量

        """
        conditions = []

        if category is not None:
            conditions.append(SystemLog.category == category)
        if level is not None:
            conditions.append(SystemLog.level == level)
        if time_start is not None:
            conditions.append(SystemLog.timestamp >= time_start)
        if time_end is not None:
            conditions.append(SystemLog.timestamp <= time_end)
        if source_module is not None:
            conditions.append(SystemLog.source_module == source_module)
        if user_id is not None:
            conditions.append(SystemLog.user_id == user_id)
        if user_ids is not None:
            conditions.append(SystemLog.user_id.in_(user_ids))

        stmt = select(func.count(SystemLog.log_id))
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete_old_logs(self, before: datetime) -> int:
        """删除指定时间之前的日志.

        Args:
            before: 删除此时间之前的日志

        Returns:
            删除的日志数量

        """
        stmt = select(SystemLog).where(SystemLog.timestamp < before)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        count = len(logs)
        for log in logs:
            await self.session.delete(log)

        await self.session.flush()
        return count
