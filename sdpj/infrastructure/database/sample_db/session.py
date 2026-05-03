"""SampleDB 数据库会话管理

提供异步数据库会话的创建和管理功能。
使用 SQLAlchemy 2.0 异步引擎和会话。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, StaticPool
from .models import Base


class SampleDBSessionManager:
    """SampleDB 会话管理器

    负责管理数据库引擎和会话的生命周期。
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/db/sdpj.db"):
        """初始化会话管理器

        Args:
            database_url: 数据库连接 URL，默认使用 SQLite + aiosqlite
        """
        self.database_url = database_url
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        """初始化数据库引擎和会话工厂"""
        if self._engine is None:
            is_memory = ":memory:" in self.database_url
            self._engine = create_async_engine(
                self.database_url,
                echo=False,
                future=True,
                poolclass=StaticPool if is_memory else NullPool,
                connect_args={"check_same_thread": False},
            )

            if "sqlite" in self.database_url:
                @event.listens_for(self._engine.sync_engine, "connect")
                def _enable_fk(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # 提交后对象不过期
                autoflush=False,  # 手动控制 flush
                autocommit=False,  # 手动控制 commit
            )

    async def create_tables(self) -> None:
        """创建所有数据表

        注意：仅用于开发和测试环境。
        生产环境应使用 Alembic 迁移管理数据库结构。
        """
        if self._engine is None:
            await self.initialize()

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """删除所有数据表

        警告：此操作会删除所有数据，仅用于测试环境。
        """
        if self._engine is None:
            await self.initialize()

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）

        使用示例：
            async with session_manager.get_session() as session:
                # 执行数据库操作
                result = await session.execute(...)
                await session.commit()

        Yields:
            AsyncSession: 异步数据库会话
        """
        if self._session_factory is None:
            await self.initialize()

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """关闭数据库引擎

        释放所有数据库连接资源。
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局会话管理器实例（单例模式）
_session_manager: Optional[SampleDBSessionManager] = None


def get_session_manager(database_url: str = "sqlite+aiosqlite:///./data/db/sdpj.db") -> SampleDBSessionManager:
    """获取全局会话管理器实例

    Args:
        database_url: 数据库连接 URL

    Returns:
        SampleDBSessionManager: 会话管理器实例
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SampleDBSessionManager(database_url)
    return _session_manager
