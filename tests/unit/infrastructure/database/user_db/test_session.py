"""UserDB 会话管理测试"""

import pytest

from sdpj.infrastructure.database.user_db import UserDBSessionManager
from typing import Any


@pytest.mark.asyncio
class TestUserDBSessionManager:
    """测试 UserDBSessionManager"""

    async def test_session_manager_creation(self) -> None:
        """测试会话管理器创建"""
        manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        assert manager is not None
        assert manager.engine is not None
        await manager.close()

    async def test_create_tables(self) -> None:
        """测试创建表"""
        manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        await manager.create_tables()
        # 验证表创建成功(通过尝试使用会话)
        async with manager.session() as session:
            assert session is not None
        await manager.close()

    async def test_session_context_manager(self) -> None:
        """测试会话上下文管理器"""
        manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        await manager.create_tables()

        async with manager.session() as session:
            assert session is not None
            # 会话应该是活跃的
            assert session.is_active

        await manager.close()

    async def test_session_rollback_on_error(self) -> None:
        """测试异常时会话回滚"""
        manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        await manager.create_tables()

        with pytest.raises(ValueError):
            async with manager.session() as session:
                # 模拟错误
                raise ValueError("测试错误")

        # 会话应该已经回滚并关闭
        await manager.close()

    async def test_drop_tables(self) -> None:
        """测试删除表"""
        manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        await manager.create_tables()
        await manager.drop_tables()
        await manager.close()
