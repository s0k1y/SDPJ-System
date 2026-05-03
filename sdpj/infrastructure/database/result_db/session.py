"""ResultDB 数据库会话管理

提供异步数据库会话的创建和管理。
"""

from typing import AsyncGenerator, Optional
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


class SessionManager:
    """数据库会话管理器

    负责创建和管理异步数据库引擎和会话。
    """

    def __init__(self, database_url: str, echo: bool = False):
        """初始化会话管理器

        Args:
            database_url: 数据库连接URL
            echo: 是否输出SQL语句
        """
        self.database_url = database_url
        self.echo = echo
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker = None

    async def initialize(self) -> None:
        """初始化数据库引擎和会话工厂"""
        if self.engine is None:
            is_memory = ":memory:" in self.database_url
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                future=True,
                poolclass=StaticPool if is_memory else NullPool,
                connect_args={"check_same_thread": False},
            )

            if "sqlite" in self.database_url:
                @event.listens_for(self.engine.sync_engine, "connect")
                def _enable_fk(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

    async def create_tables(self) -> None:
        """创建所有表"""
        if self.engine is None:
            await self.initialize()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """删除所有表"""
        if self.engine is None:
            await self.initialize()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话的上下文管理器"""
        if self.async_session_maker is None:
            await self.initialize()
        async with self.async_session_maker() as session:
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
        if self.engine:
            await self.engine.dispose()
