"""AccountManager 单元测试"""

import pytest
from unittest.mock import AsyncMock

from sdpj.core.account_manager import AccountManager
from typing import Any


def _uc(**overrides: Any) -> None:
    """测试 uc."""
    uc = AsyncMock()
    for k, v in overrides.items():
        setattr(uc, k, AsyncMock(side_effect=v))
    return uc


@pytest.mark.asyncio
class TestRegister:
    """测试 TestRegister 类."""

    async def test_success(self) -> None:
        """测试 test success."""
        mgr = AccountManager(_uc(register_user=lambda u, p: 1))
        ok, uid, msg = await mgr.register("alice", "password123")
        assert ok and uid == 1 and msg == ""

    async def test_username_too_short(self) -> None:
        """测试 test username too short."""
        mgr = AccountManager(AsyncMock())
        ok, uid, _ = await mgr.register("ab", "password123")
        assert not ok and uid is None

    async def test_password_too_short(self) -> None:
        """测试 test password too short."""
        mgr = AccountManager(AsyncMock())
        ok, uid, _ = await mgr.register("alice", "123")
        assert not ok and uid is None

    async def test_duplicate_raises(self) -> None:
        """测试 test duplicate raises."""
        def _raise(u: Any, p: Any) -> None:
            """测试 raise."""
            raise ValueError("已存在")

        mgr = AccountManager(_uc(register_user=_raise))
        ok, uid, msg = await mgr.register("alice", "password123")
        assert not ok and uid is None and "已存在" in msg


@pytest.mark.asyncio
class TestLogin:
    """测试 TestLogin 类."""

    async def test_success(self) -> None:
        """测试 test success."""
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: (True, 42, "")))
        ok, uid, _ = await mgr.login("alice", "password123")
        assert ok and uid == 42 and mgr.get_current_session() == 42

    async def test_wrong_password(self) -> None:
        """测试 test wrong password."""
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: (False, None, "密码错误")))
        ok, uid, _ = await mgr.login("alice", "wrong")
        assert not ok and uid is None


@pytest.mark.asyncio
class TestLogout:
    """测试 TestLogout 类."""

    async def test_when_logged_in(self) -> None:
        """测试 test when logged in."""
        mgr = AccountManager(_uc(verify_credentials=lambda u, p: (True, 1, "")))
        await mgr.login("alice", "pw123456")
        assert mgr.logout() is True
        assert mgr.get_current_session() is None

    async def test_when_not_logged_in(self) -> None:
        """测试 test when not logged in."""
        assert AccountManager(AsyncMock()).logout() is False


@pytest.mark.asyncio
class TestChangePassword:
    """测试 TestChangePassword 类."""

    async def test_user_not_found(self) -> None:
        """测试 test user not found."""
        mgr = AccountManager(
            _uc(
                get_user_by_id=lambda uid: None,
            )
        )
        ok, msg = await mgr.change_password_for_user(0, "old", "newpass123")
        assert not ok

    async def test_wrong_old_password(self) -> None:
        """测试 test wrong old password."""
        mgr = AccountManager(
            _uc(
                get_user_by_id=lambda uid: {"username": "alice"},
                verify_credentials=lambda u, p: (False, None, "密码错误"),
            )
        )
        ok, _ = await mgr.change_password_for_user(1, "wrong", "newpass123")
        assert not ok

    async def test_success(self) -> None:
        """测试 test success."""
        mgr = AccountManager(
            _uc(
                get_user_by_id=lambda uid: {"username": "alice"},
                verify_credentials=lambda u, p: (True, 1, ""),
                update_user_password=lambda uid, pw: True,
            )
        )
        ok, _ = await mgr.change_password_for_user(1, "old", "newpass123")
        assert ok
