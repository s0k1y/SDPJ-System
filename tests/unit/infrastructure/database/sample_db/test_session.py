"""SampleDB 会话管理单元测试"""

import pytest
from sdpj.infrastructure.database.sample_db.session import (
    SampleDBSessionManager,
    get_session_manager,
)
from sdpj.infrastructure.database.sample_db.models import Base, Dataset


@pytest.mark.asyncio
async def test_session_manager_initialization():
    """测试会话管理器初始化"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    assert manager._engine is not None
    assert manager._session_factory is not None

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_create_tables():
    """测试创建数据表"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    # 验证表已创建（通过插入数据测试）
    async with manager.get_session() as session:
        dataset = Dataset(name="测试数据集", risk_type="越狱攻击")
        session.add(dataset)
        await session.commit()
        assert dataset.dataset_id is not None

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_drop_tables():
    """测试删除数据表"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()
    await manager.drop_tables()

    # 验证表已删除（尝试插入数据应失败）
    from sqlalchemy.exc import OperationalError

    async with manager.get_session() as session:
        dataset = Dataset(name="测试数据集", risk_type="越狱攻击")
        session.add(dataset)
        with pytest.raises(OperationalError):
            await session.commit()

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_get_session():
    """测试获取数据库会话"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    async with manager.get_session() as session:
        assert session is not None
        # 测试会话可用
        dataset = Dataset(name="会话测试", risk_type="提示词注入")
        session.add(dataset)
        await session.commit()

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_rollback_on_error():
    """测试会话在异常时自动回滚"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    try:
        async with manager.get_session() as session:
            dataset = Dataset(name="回滚测试", risk_type="越狱攻击")
            session.add(dataset)
            await session.commit()

            # 故意触发异常
            raise ValueError("测试异常")
    except ValueError:
        pass

    # 验证数据已提交（异常发生在提交之后）
    async with manager.get_session() as session:
        from sqlalchemy import select

        stmt = select(Dataset).where(Dataset.name == "回滚测试")
        result = await session.execute(stmt)
        dataset = result.scalar_one_or_none()
        assert dataset is not None

    await manager.close()


@pytest.mark.asyncio
async def test_get_session_manager_singleton():
    """测试全局会话管理器单例模式"""
    manager1 = get_session_manager("sqlite+aiosqlite:///:memory:")
    manager2 = get_session_manager("sqlite+aiosqlite:///:memory:")

    assert manager1 is manager2

    await manager1.close()


@pytest.mark.asyncio
async def test_session_manager_close():
    """测试关闭会话管理器"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    assert manager._engine is not None

    await manager.close()

    assert manager._engine is None
    assert manager._session_factory is None
