"""ResultDB 会话管理单元测试

测试数据库会话管理器的功能.
"""

import pytest
from sdpj.infrastructure.database.result_db.session import SessionManager
from sdpj.infrastructure.database.result_db.models import Base, TaskGroup, TargetModel
from typing import Any


@pytest.fixture
async def session_manager() -> None:
    """创建测试用的会话管理器"""
    manager = SessionManager("sqlite+aiosqlite:///:memory:", echo=False)
    await manager.create_tables()
    from sdpj.infrastructure.database.user_db.models import User

    async with manager.session() as session:
        session.add(User(username="test_user", password="pw"))
        session.add(TargetModel(model_id="m1"))
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_initialization() -> None:
    """测试会话管理器初始化"""
    manager = SessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    assert manager.engine is not None
    assert manager.async_session_maker is not None
    await manager.close()


@pytest.mark.asyncio
async def test_create_tables(session_manager: Any) -> None:
    """测试创建表"""
    async with session_manager.session() as session:
        tg = TaskGroup(task_group_id="test-tg", user_id=1, model_id="m1")
        session.add(tg)
        await session.commit()

        from sqlalchemy import select

        result = await session.execute(
            select(TaskGroup).where(TaskGroup.task_group_id == "test-tg")
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.task_group_id == "test-tg"


@pytest.mark.asyncio
async def test_session_context_manager(session_manager: Any) -> None:
    """测试会话上下文管理器"""
    async with session_manager.session() as session:
        tg = TaskGroup(task_group_id="context-test", user_id=1, model_id="m1")
        session.add(tg)

    async with session_manager.session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(TaskGroup).where(TaskGroup.task_group_id == "context-test")
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None


@pytest.mark.asyncio
async def test_session_rollback_on_exception(session_manager: Any) -> None:
    """测试异常时自动回滚"""
    try:
        async with session_manager.session() as session:
            tg = TaskGroup(task_group_id="rollback-test", user_id=1, model_id="m1")
            session.add(tg)
            await session.flush()
            raise ValueError("Test exception")
    except ValueError:
        pass

    async with session_manager.session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(TaskGroup).where(TaskGroup.task_group_id == "rollback-test")
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is None


@pytest.mark.asyncio
async def test_drop_tables() -> None:
    """测试删除表"""
    from sdpj.infrastructure.database.user_db.models import User

    manager = SessionManager("sqlite+aiosqlite:///:memory:")
    await manager.create_tables()

    async with manager.session() as session:
        session.add(User(username="u", password="pw"))
        session.add(TargetModel(model_id="m1"))
        await session.flush()
        tg = TaskGroup(task_group_id="drop-test", user_id=1, model_id="m1")
        session.add(tg)

    await manager.drop_tables()
    await manager.create_tables()

    async with manager.session() as session:
        from sqlalchemy import select

        result = await session.execute(select(TaskGroup))
        items = result.scalars().all()
        assert len(items) == 0

    await manager.close()
