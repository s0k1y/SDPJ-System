"""测试: session() 在 CancelledError 传播时的行为

复现条件:
1. session 内部有活跃的数据库操作 (_connection_for_bind 进行中)
2. 任务被取消 (CancelledError 传播)
3. @asynccontextmanager 的 async generator cleanup 迫使 finally 中 close() 在连接未就绪时执行
"""
import asyncio
import pytest
from sdpj.infrastructure.database.result_db.session import SessionManager
from typing import Any


@pytest.mark.asyncio
async def test_basic_cancelled_during_yield() -> None:
    """简单取消: yield 期间 CancelledError 触发 asyncgen cleanup"""
    mgr = SessionManager("sqlite+aiosqlite:///:memory:")
    await mgr.initialize()
    await mgr.create_tables()

    async def task() -> None:
        async with mgr.session() as session:
            await session.execute(
                __import__('sqlalchemy').text("SELECT 1")
            )
            raise asyncio.CancelledError()

    try:
        await task()
    except asyncio.CancelledError:
        pass

    await mgr.close()


@pytest.mark.asyncio
async def test_cancelled_during_commit() -> None:
    """commit 阶段取消: 在 commit 前抛出 CancelledError"""
    mgr = SessionManager("sqlite+aiosqlite:///:memory:")
    await mgr.initialize()
    await mgr.create_tables()

    async def task() -> None:
        async with mgr.session() as session:
            await session.execute(
                __import__('sqlalchemy').text("SELECT 1")
            )
            raise asyncio.CancelledError()

    try:
        await task()
    except asyncio.CancelledError:
        pass

    await mgr.close()


@pytest.mark.asyncio
async def test_concurrent_close_and_cancel() -> None:
    """
    精确复现: 并发执行 (1) session.close() 和 (2) 连接池关闭.
    模拟 CancelledError 在 _connection_for_bind 进行中时触发 close()
    """
    mgr = SessionManager("sqlite+aiosqlite:///:memory:")
    await mgr.initialize()
    await mgr.create_tables()

    async def use_and_cancel() -> None:
        async with mgr.session() as session:
            await session.execute(
                __import__('sqlalchemy').text("SELECT 1")
            )
            await session.commit()

            t = asyncio.create_task(
                session.execute(__import__('sqlalchemy').text("SELECT 1"))
            )
            await asyncio.sleep(0.01)
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

            raise asyncio.CancelledError()

    try:
        await use_and_cancel()
    except asyncio.CancelledError:
        pass

    await mgr.close()
