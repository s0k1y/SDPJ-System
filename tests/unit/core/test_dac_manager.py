"""DACManager 单元测试"""

import pytest
from unittest.mock import AsyncMock

from sdpj.core.dac_manager import DACManager
from typing import Any


def _uc(**overrides: Any) -> None:
    """测试 uc."""
    uc = AsyncMock()
    for k, v in overrides.items():
        setattr(uc, k, AsyncMock(side_effect=v))
    return uc


@pytest.mark.asyncio
class TestGrantAccess:
    """测试 TestGrantAccess 类."""

    async def test_resource_not_found(self) -> None:
        """测试 test resource not found."""
        mgr = DACManager(_uc(get_resource_by_id=lambda rid: None))
        ok, msg = await mgr.grant_access(1, 2, 3)
        assert not ok and "不存在" in msg

    async def test_not_owner(self) -> None:
        """测试 test not owner."""
        mgr = DACManager(_uc(get_resource_by_id=lambda rid: {"owner_user_id": 99}))
        ok, msg = await mgr.grant_access(1, 2, caller_user_id=1)
        assert not ok and "拥有者" in msg

    async def test_already_has_access(self) -> None:
        """测试 test already has access."""
        mgr = DACManager(
            _uc(
                get_resource_by_id=lambda rid: {"owner_user_id": 1},
                check_access=lambda rid, uid: True,
            )
        )
        ok, msg = await mgr.grant_access(1, 2, caller_user_id=1)
        assert not ok and "已拥有" in msg

    async def test_success(self) -> None:
        """测试 test success."""
        mgr = DACManager(
            _uc(
                get_resource_by_id=lambda rid: {"owner_user_id": 1},
                check_access=lambda rid, uid: False,
                grant_access=lambda rid, uid: 10,
            )
        )
        ok, acl_id = await mgr.grant_access(1, 2, caller_user_id=1)
        assert ok and acl_id == "10"


@pytest.mark.asyncio
class TestCheckAccess:
    """测试 TestCheckAccess 类."""

    async def test_owner_always_has_access(self) -> None:
        """测试 test owner always has access."""
        mgr = DACManager(_uc(get_resource_by_id=lambda rid: {"owner_user_id": 5}))
        assert await mgr.check_access(1, user_id=5) is True

    async def test_non_owner_delegates(self) -> None:
        """测试 test non owner delegates."""
        mgr = DACManager(
            _uc(
                get_resource_by_id=lambda rid: {"owner_user_id": 1},
                check_access=lambda rid, uid: True,
            )
        )
        assert await mgr.check_access(1, user_id=2) is True

    async def test_resource_missing(self) -> None:
        """测试 test resource missing."""
        mgr = DACManager(_uc(get_resource_by_id=lambda rid: None))
        assert await mgr.check_access(1, user_id=2) is False


@pytest.mark.asyncio
class TestRevokeAccess:
    """测试 TestRevokeAccess 类."""

    async def test_acl_not_found(self) -> None:
        """测试 test acl not found."""
        mgr = DACManager(_uc(get_acl_by_id=lambda aid: None))
        ok, msg = await mgr.revoke_access(1, caller_user_id=1)
        assert not ok and "不存在" in msg

    async def test_not_owner(self) -> None:
        """测试 test not owner."""
        mgr = DACManager(
            _uc(
                get_acl_by_id=lambda aid: {"resource_id": 10},
                get_resource_by_id=lambda rid: {"owner_user_id": 99},
            )
        )
        ok, msg = await mgr.revoke_access(1, caller_user_id=1)
        assert not ok and "拥有者" in msg

    async def test_success(self) -> None:
        """测试 test success."""
        mgr = DACManager(
            _uc(
                get_acl_by_id=lambda aid: {"resource_id": 10},
                get_resource_by_id=lambda rid: {"owner_user_id": 1},
                revoke_access=lambda aid: True,
            )
        )
        ok, _ = await mgr.revoke_access(1, caller_user_id=1)
        assert ok
