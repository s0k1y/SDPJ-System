"""数据库集成测试 — UserRepository + PrivateConfigRepository"""

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from sdpj.infrastructure.database.user_db.models import Base
from sdpj.infrastructure.database.user_db.repositories.user_repo import UserRepository
from sdpj.infrastructure.database.user_db.repositories.resource_repo import ResourceRepository
from sdpj.infrastructure.database.user_db.repositories.private_config_repo import (
    PrivateConfigRepository,
)


@pytest_asyncio.fixture
async def session():  # noqa: ANN201, D103
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _fk(conn, _) -> None:  # noqa: ANN001
        conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


@pytest.mark.asyncio
class TestUserRepository:  # noqa: D101
    async def test_create_and_get(self, session) -> None:  # noqa: ANN001, D102
        repo = UserRepository(session)
        user = await repo.create("alice", "hashed_pw")
        await session.commit()
        found = await repo.get_by_username("alice")
        assert found is not None and found.user_id == user.user_id

    async def test_duplicate_raises(self, session) -> None:  # noqa: ANN001, D102
        repo = UserRepository(session)
        await repo.create("bob", "pw")
        await session.commit()
        with pytest.raises(ValueError, match="已存在"):
            await repo.create("bob", "pw2")

    async def test_delete(self, session) -> None:  # noqa: ANN001, D102
        repo = UserRepository(session)
        user = await repo.create("carol", "pw")
        await session.commit()
        deleted = await repo.delete(user.user_id)
        await session.commit()
        assert deleted is True
        assert await repo.get_by_id(user.user_id) is None

    async def test_update_password(self, session) -> None:  # noqa: ANN001, D102
        repo = UserRepository(session)
        user = await repo.create("dave", "old_pw")
        await session.commit()
        ok = await repo.update_password(user.user_id, "new_pw")
        await session.commit()
        assert ok
        updated = await repo.get_by_id(user.user_id)
        assert updated.password == "new_pw"

    async def test_get_nonexistent(self, session) -> None:  # noqa: ANN001, D102
        assert await UserRepository(session).get_by_id(9999) is None


@pytest.mark.asyncio
class TestPrivateConfigRepository:  # noqa: D101
    async def _make_resource(self, session, owner_id: int) -> int:  # noqa: ANN001
        user_repo = UserRepository(session)
        user = await user_repo.create(f"owner_{owner_id}", "pw")
        await session.commit()
        res_repo = ResourceRepository(session)
        resource = await res_repo.create("config", user.user_id)
        await session.commit()
        return resource.resource_id

    async def test_create_and_read(self, session) -> None:  # noqa: ANN001, D102
        rid = await self._make_resource(session, 1)
        repo = PrivateConfigRepository(session)
        await repo.create(rid, {"model_id": "gpt-4", "api_key": "sk-test"})
        await session.commit()
        data = await repo.get_by_id(rid)
        assert data["model_id"] == "gpt-4"

    async def test_update(self, session) -> None:  # noqa: ANN001, D102
        rid = await self._make_resource(session, 2)
        repo = PrivateConfigRepository(session)
        await repo.create(rid, {"v": 1})
        await session.commit()
        await repo.update(rid, {"v": 2})
        await session.commit()
        assert (await repo.get_by_id(rid))["v"] == 2

    async def test_delete(self, session) -> None:  # noqa: ANN001, D102
        rid = await self._make_resource(session, 3)
        repo = PrivateConfigRepository(session)
        await repo.create(rid, {"v": 1})
        await session.commit()
        ok = await repo.delete(rid)
        await session.commit()
        assert ok and await repo.get_by_id(rid) is None
