"""UserDB 单元测试配置和夹具"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager


@pytest_asyncio.fixture
async def session_manager():
    """创建测试用的会话管理器（使用内存数据库）"""
    manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:", echo=False)
    await manager.create_tables()
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def user_db(session_manager):
    """创建 UserDB 实例"""
    return UserDB(session_manager)


@pytest_asyncio.fixture
async def sample_user(user_db):
    """创建示例用户"""
    user_id = await user_db.create_user("testuser", "hashed_password_123")
    return {"user_id": user_id, "username": "testuser", "password_hash": "hashed_password_123"}


@pytest_asyncio.fixture
async def sample_resource(user_db, sample_user):
    """创建示例资源"""
    resource_id = await user_db.register_resource("private_config", sample_user["user_id"])
    return {"resource_id": resource_id, "resource_type": "private_config", "owner_user_id": sample_user["user_id"]}
