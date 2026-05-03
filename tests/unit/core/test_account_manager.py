"""AccountManager 单元测试"""
import pytest
from unittest.mock import AsyncMock

from sdpj.core.account_manager import AccountManager


def _uc(**overrides):
    uc = AsyncMock()
    for k, v in overrides.items():
        setattr(uc, k, AsyncMock(side_effect=v))
    return uc


@pytest.mark.asyncio
class TestRegister:
    async def test_success(self):
        mgr = AccountManager(_uc(register_user=lambda u, p: 1))
        ok, msg = await mgr.register("alice", "password123")
        assert ok and msg == "1"

    async def test_username_too_short(self):
        mgr = AccountManager(AsyncMock())
        ok, _ = await mgr.register("ab", "password123")
        assert not ok

    async def test_password_too_short(self):
        mgr = AccountManager(AsyncMock())
        ok, _ = await mgr.register("alice", "123")
        assert not ok

    async def test_duplicate_raises(self):
        def _raise(u, p): raise ValueError("已存在")
        mgr = AccountManager(_uc(register_user=_raise))
        ok, msg = await mgr.register("alice", "password123")
        assert not ok and "已存在" in msg


@pytest.mark.asyncio
class TestLogin:
    async def test_success(self):
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: 42))
        ok, uid = await mgr.login("alice", "password123")
        assert ok and uid == 42 and mgr.get_current_session() == 42

    async def test_wrong_password(self):
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: None))
        ok, uid = await mgr.login("alice", "wrong")
        assert not ok and uid is None


@pytest.mark.asyncio
class TestLogout:
    async def test_when_logged_in(self):
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: 1))
        await mgr.login("alice", "pw123456")
        assert mgr.logout() is True
        assert mgr.get_current_session() is None

    async def test_when_not_logged_in(self):
        assert AccountManager(AsyncMock()).logout() is False


@pytest.mark.asyncio
class TestChangePassword:
    async def test_not_logged_in(self):
        ok, msg = await AccountManager(AsyncMock()).change_password("old", "newpass123")
        assert not ok and "未登录" in msg

    async def test_wrong_old_password(self):
        mgr = AccountManager(_uc(
            verify_credentials=lambda u, p: None,
            get_user_by_id=lambda uid: {"username": "alice"},
        ))
        mgr._current_user_id = 1
        ok, _ = await mgr.change_password("wrong", "newpass123")
        assert not ok

    async def test_success(self):
        mgr = AccountManager(_uc(
            verify_credentials=lambda u, p: 1,
            get_user_by_id=lambda uid: {"username": "alice"},
            update_user_password=lambda uid, pw: True,
        ))
        mgr._current_user_id = 1
        ok, _ = await mgr.change_password("old", "newpass123")
        assert ok
