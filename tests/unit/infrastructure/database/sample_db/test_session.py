"""SampleDB 浼氳瘽绠＄悊鍗曞厓娴嬭瘯"""

import pytest
from sdpj.infrastructure.database.sample_db.session import (
    SampleDBSessionManager,
    get_session_manager,
)
from sdpj.infrastructure.database.sample_db.models import Base, Dataset
from typing import Any


@pytest.mark.asyncio
async def test_session_manager_initialization() -> None:
    """娴嬭瘯浼氳瘽绠＄悊鍣ㄥ垵濮嬪寲"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    assert manager._engine is not None
    assert manager._session_factory is not None

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_create_tables() -> None:
    """娴嬭瘯鍒涘缓鏁版嵁琛?""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    # 楠岃瘉琛ㄥ凡鍒涘缓(閫氳繃鎻掑叆鏁版嵁娴嬭瘯)
    async with manager.session() as session:
        dataset = Dataset(name="娴嬭瘯鏁版嵁闆?, risk_type="瓒婄嫳鏀诲嚮")
        session.add(dataset)
        await session.commit()
        assert dataset.dataset_id is not None

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_drop_tables() -> None:
    """娴嬭瘯鍒犻櫎鏁版嵁琛?""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()
    await manager.drop_tables()

    from sqlalchemy.exc import OperationalError

    session = manager._session_factory()
    try:
        dataset = Dataset(name="娴嬭瘯鏁版嵁闆?, risk_type="瓒婄嫳鏀诲嚮")
        session.add(dataset)
        with pytest.raises(OperationalError):
            await session.commit()
    finally:
        await session.rollback()
        await session.close()

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_get_session() -> None:
    """娴嬭瘯鑾峰彇鏁版嵁搴撲細璇?""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    async with manager.session() as session:
        assert session is not None
        # 娴嬭瘯浼氳瘽鍙敤
        dataset = Dataset(name="浼氳瘽娴嬭瘯", risk_type="鎻愮ず璇嶆敞鍏?)
        session.add(dataset)
        await session.commit()

    await manager.close()


@pytest.mark.asyncio
async def test_session_manager_rollback_on_error() -> None:
    """娴嬭瘯浼氳瘽鍦ㄥ紓甯告椂鑷姩鍥炴粴"""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    await manager.create_tables()

    try:
        async with manager.session() as session:
            dataset = Dataset(name="鍥炴粴娴嬭瘯", risk_type="瓒婄嫳鏀诲嚮")
            session.add(dataset)
            await session.commit()

            # 鏁呮剰瑙﹀彂寮傚父
            raise ValueError("娴嬭瘯寮傚父")
    except ValueError:
        pass

    # 楠岃瘉鏁版嵁宸叉彁浜?寮傚父鍙戠敓鍦ㄦ彁浜や箣鍚?
    async with manager.session() as session:
        from sqlalchemy import select

        stmt = select(Dataset).where(Dataset.name == "鍥炴粴娴嬭瘯")
        result = await session.execute(stmt)
        dataset = result.scalar_one_or_none()
        assert dataset is not None

    await manager.close()


@pytest.mark.asyncio
async def test_get_session_manager_singleton() -> None:
    """娴嬭瘯鍏ㄥ眬浼氳瘽绠＄悊鍣ㄥ崟渚嬫ā寮?""
    manager1 = get_session_manager("sqlite+aiosqlite:///:memory:")
    manager2 = get_session_manager("sqlite+aiosqlite:///:memory:")

    assert manager1 is manager2

    await manager1.close()


@pytest.mark.asyncio
async def test_session_manager_close() -> None:
    """娴嬭瘯鍏抽棴浼氳瘽绠＄悊鍣?""
    manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()

    assert manager._engine is not None

    await manager.close()

    assert manager._engine is None
    assert manager._session_factory is None
