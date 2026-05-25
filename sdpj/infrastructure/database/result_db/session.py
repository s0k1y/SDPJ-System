"""ResultDB 数据库会话管理

提供异步数据库会话的创建和管理。
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from .models import Base


class SessionManager:
    """数据库会话管理器

    负责创建和管理异步数据库引擎和会话。
    """

    def __init__(self, database_url: str, echo: bool = False, engine: Optional[AsyncEngine] = None):
        self.database_url = database_url
        self.echo = echo
        self.engine: Optional[AsyncEngine] = engine
        self.async_session_maker = None
        if engine is not None:
            self.async_session_maker = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

    async def initialize(self) -> None:
        """初始化数据库引擎和会话工厂"""
        if self.engine is None:
            is_memory = ":memory:" in self.database_url
            pool_kwargs: dict[str, object]
            if is_memory:
                pool_kwargs = {"poolclass": StaticPool}
            else:
                pool_kwargs = {"pool_size": 5, "max_overflow": 0}
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                future=True,
                **pool_kwargs,
                connect_args={"check_same_thread": False},
            )

            if "sqlite" in self.database_url:

                @event.listens_for(self.engine.sync_engine, "connect")
                def _set_pragmas(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA busy_timeout=5000")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.close()

            self.async_session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

    async def create_tables(self) -> None:
        from sdpj.infrastructure.database.result_db.models import SystemLog  # noqa
        from sdpj.infrastructure.database.sample_db.models import Dataset  # noqa
        from sdpj.infrastructure.database.user_db.models import User  # noqa

        if self.engine is None:
            await self.initialize()
        assert self.engine is not None
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self._migrate_detection_task(conn)
            await self._migrate_timestamps_to_utc(conn)

    async def _migrate_detection_task(self, conn) -> None:
        """为 DetectionTask 表补充 algorithm_type、metadata_json 和 error_message 列"""
        try:
            result = await conn.exec_driver_sql("PRAGMA table_info('DetectionTask')")
            columns = {row[1] for row in await result.fetchall()}
            if "algorithm_type" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE DetectionTask ADD COLUMN algorithm_type VARCHAR(20) NOT NULL DEFAULT 'static'"
                )
            if "metadata_json" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE DetectionTask ADD COLUMN metadata_json JSON"
                )
            if "error_message" not in columns:
                await conn.exec_driver_sql(
                    "ALTER TABLE DetectionTask ADD COLUMN error_message TEXT"
                )
        except Exception:
            pass

    async def _migrate_timestamps_to_utc(self, conn) -> None:
        """将旧本地时间戳迁移为UTC-naive格式

        旧日志使用本地时间(naive datetime)存储，新日志使用UTC时间存储。
        此迁移将所有时间戳统一为UTC-naive格式，确保排序正确。
        使用 _utc_migrated 标记避免重复迁移。
        """
        try:
            result = await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='_utc_migrated'"
            )
            if result.fetchall():
                return

            local_offset = datetime.now().astimezone().utcoffset()
            if local_offset is None:
                local_offset = __import__("datetime").timedelta(0)

            for table_name, ts_columns in [
                ("SystemLog", ["timestamp"]),
                ("DetectionTask", ["start_time", "end_time"]),
            ]:
                result = await conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                if not result.fetchall():
                    continue

                result = await conn.exec_driver_sql(f"SELECT COUNT(*) FROM {table_name}")
                total = (await result.fetchone())[0]
                if total == 0:
                    continue

                pk_result = await conn.exec_driver_sql(f"PRAGMA table_info('{table_name}')")
                pk_col = None
                for col_info in await pk_result.fetchall():
                    if col_info[5]:
                        pk_col = col_info[1]
                        break
                if pk_col is None:
                    continue

                for col in ts_columns:
                    result = await conn.exec_driver_sql(
                        f"SELECT {pk_col}, {col} FROM {table_name} WHERE {col} IS NOT NULL"
                    )
                    rows = await result.fetchall()
                    for row in rows:
                        pk_val = row[0]
                        ts_val = row[1]
                        if ts_val is None:
                            continue

                        new_ts = self._normalize_timestamp(ts_val, local_offset)
                        if new_ts is not None:
                            await conn.exec_driver_sql(
                                f"UPDATE {table_name} SET {col} = ? WHERE {pk_col} = ?",
                                (new_ts, pk_val),
                            )

            await conn.exec_driver_sql(
                "CREATE TABLE _utc_migrated (done INTEGER NOT NULL DEFAULT 1)"
            )
            await conn.exec_driver_sql("INSERT INTO _utc_migrated (done) VALUES (1)")
        except Exception:
            pass

    @staticmethod
    def _normalize_timestamp(ts_val, local_offset) -> str | None:
        """将时间戳值归一化为UTC-naive格式字符串

        Args:
            ts_val: 数据库中的时间戳值(str或datetime)
            local_offset: 本地时区偏移(timedelta)

        Returns:
            UTC-naive格式字符串，或None表示无需转换
        """
        try:
            if isinstance(ts_val, str):
                has_tz = "+" in ts_val[10:] or ts_val.endswith("Z")
                if has_tz:
                    dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                    utc_naive = dt.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    dt = datetime.fromisoformat(ts_val)
                    utc_naive = dt - local_offset
            elif isinstance(ts_val, datetime):
                if ts_val.tzinfo is not None:
                    utc_naive = ts_val.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    utc_naive = ts_val - local_offset
            else:
                return None

            return utc_naive.strftime("%Y-%m-%d %H:%M:%S.%f")
        except (ValueError, OverflowError):
            return None

    async def drop_tables(self) -> None:
        """删除所有表"""
        if self.engine is None:
            await self.initialize()
        assert self.engine is not None
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话的上下文管理器"""
        if self.async_session_maker is None:
            await self.initialize()
        assert self.async_session_maker is not None
        session: AsyncSession = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception:
                pass

    async def close(self) -> None:
        """关闭数据库引擎"""
        if self.engine:
            await self.engine.dispose()
