"""UserDB 数据库会话管理

基于 SQLAlchemy 2.0 异步 API 的会话管理。
使用 aiosqlite 作为异步 SQLite 驱动。
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, StaticPool

from .models import Base


class UserDBSessionManager:
    """UserDB 会话管理器

    职责：
    - 管理数据库引擎生命周期
    - 提供异步会话工厂
    - 提供会话上下文管理器
    """

    def __init__(self, database_url: str, echo: bool = False, engine: AsyncEngine = None):
        if engine is not None:
            self._engine = engine
        else:
            is_memory = ":memory:" in database_url
            self._engine: AsyncEngine = create_async_engine(
                database_url,
                echo=echo,
                poolclass=StaticPool if is_memory else NullPool,
                connect_args={"check_same_thread": False}
            )
            if "sqlite" in database_url:
                @event.listens_for(self._engine.sync_engine, "connect")
                def _enable_fk(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
        )

    async def initialize(self) -> None:
        """初始化（兼容性方法，实际在 __init__ 中已初始化）"""
        pass

    async def create_tables(self) -> None:
        """创建所有表（如果不存在）"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """删除所有表（慎用，仅用于测试）"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """提供异步会话上下文管理器

        使用示例：
            async with session_manager.session() as session:
                # 执行数据库操作
                result = await session.execute(select(User))
                await session.commit()
        """
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """关闭数据库引擎"""
        await self._engine.dispose()

    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        return self._engine
