"""UserDB 数据库会话管理

基于 SQLAlchemy 2.0 异步 API 的会话管理。
使用 aiosqlite 作为异步 SQLite 驱动。
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool

from .models import Base


class UserDBSessionManager:
    """UserDB 会话管理器

    职责：
    - 管理数据库引擎生命周期
    - 提供异步会话工厂
    - 提供会话上下文管理器
    """

    def __init__(self, database_url: str, echo: bool = False):
        """初始化会话管理器

        Args:
            database_url: 数据库连接 URL（例如：sqlite+aiosqlite:///path/to/db.sqlite）
            echo: 是否输出 SQL 日志
        """
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,  # SQLite 使用 NullPool 避免并发问题
            connect_args={"check_same_thread": False}  # SQLite 允许多线程访问
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
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
