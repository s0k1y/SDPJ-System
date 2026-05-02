"""ResultDB 会话管理单元测试

测试数据库会话管理器的功能。
"""

import pytest
from sdpj.infrastructure.database.result_db.session import SessionManager
from sdpj.infrastructure.database.result_db.models import Base, TargetModel


@pytest.fixture
async def session_manager():
    """创建测试用的会话管理器"""
    manager = SessionManager("sqlite+aiosqlite:///:memory:", echo=False)
    await manager.create_tables()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_initialization():
    """测试会话管理器初始化"""
    manager = SessionManager("sqlite+aiosqlite:///:memory:")
    assert manager.engine is not None
    assert manager.async_session_maker is not None
    await manager.close()


@pytest.mark.asyncio
async def test_create_tables(session_manager):
    """测试创建表"""
    # 表已在 fixture 中创建，验证可以使用
    async with session_manager.session() as session:
        model = TargetModel(model_id="test-model")
        session.add(model)
        await session.commit()

        # 验证数据已保存
        from sqlalchemy import select
        result = await session.execute(select(TargetModel).where(TargetModel.model_id == "test-model"))
        retrieved_model = result.scalar_one_or_none()
        assert retrieved_model is not None
        assert retrieved_model.model_id == "test-model"


@pytest.mark.asyncio
async def test_session_context_manager(session_manager):
    """测试会话上下文管理器"""
    async with session_manager.session() as session:
        model = TargetModel(model_id="context-test")
        session.add(model)
        # commit 会在上下文管理器退出时自动执行

    # 验证数据已提交
    async with session_manager.session() as session:
        from sqlalchemy import select
        result = await session.execute(select(TargetModel).where(TargetModel.model_id == "context-test"))
        retrieved_model = result.scalar_one_or_none()
        assert retrieved_model is not None


@pytest.mark.asyncio
async def test_session_rollback_on_exception(session_manager):
    """测试异常时自动回滚"""
    try:
        async with session_manager.session() as session:
            model = TargetModel(model_id="rollback-test")
            session.add(model)
            await session.flush()
            # 模拟异常
            raise ValueError("Test exception")
    except ValueError:
        pass

    # 验证数据未提交
    async with session_manager.session() as session:
        from sqlalchemy import select
        result = await session.execute(select(TargetModel).where(TargetModel.model_id == "rollback-test"))
        retrieved_model = result.scalar_one_or_none()
        assert retrieved_model is None


@pytest.mark.asyncio
async def test_drop_tables():
    """测试删除表"""
    manager = SessionManager("sqlite+aiosqlite:///:memory:")
    await manager.create_tables()

    # 添加数据
    async with manager.session() as session:
        model = TargetModel(model_id="drop-test")
        session.add(model)

    # 删除表
    await manager.drop_tables()

    # 重新创建表（应该是空的）
    await manager.create_tables()

    async with manager.session() as session:
        from sqlalchemy import select
        result = await session.execute(select(TargetModel))
        models = result.scalars().all()
        assert len(models) == 0

    await manager.close()
