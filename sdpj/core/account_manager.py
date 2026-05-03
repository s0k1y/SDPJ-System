"""AccountManager 用户账号管理模块

依赖模块: UserCenter (via interface)
被依赖模块: StateScheduler
"""
from typing import Optional

from sdpj.drivers.user_center_interface import UserCenterInterface


class AccountManager:
    """用户账号管理模块实现"""

    def __init__(self, user_center: UserCenterInterface):
        self._user_center = user_center
        self._current_user_id: Optional[int] = None

    async def register(self, username: str, password: str) -> tuple[bool, str]:
        if not username or len(username) < 3:
            return False, "账号长度至少3个字符"
        if not password or len(password) < 6:
            return False, "密码长度至少6个字符"
        try:
            user_id = await self._user_center.register_user(username, password)
            return True, str(user_id)
        except ValueError as e:
            return False, str(e)

    async def unregister(self, user_id: int) -> tuple[bool, str]:
        try:
            if self._current_user_id == user_id:
                self._current_user_id = None
            success = await self._user_center.delete_user(user_id)
            return (True, "") if success else (False, "注销失败")
        except Exception as e:
            return False, str(e)

    async def login(self, username: str, password: str) -> tuple[bool, Optional[int]]:
        user_id = await self._user_center.verify_credentials(username, password)
        if user_id is not None:
            self._current_user_id = user_id
            return True, user_id
        return False, None

    def get_current_session(self) -> Optional[int]:
        return self._current_user_id

    def logout(self) -> bool:
        if self._current_user_id is not None:
            self._current_user_id = None
            return True
        return False

    async def change_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        if self._current_user_id is None:
            return False, "未登录"
        if not new_password or len(new_password) < 6:
            return False, "新密码长度至少6个字符"

        user = await self._user_center.get_user_by_id(self._current_user_id)
        if not user:
            return False, "用户不存在"

        verified = await self._user_center.verify_credentials(user["username"], old_password)
        if not verified:
            return False, "原密码不正确"

        success = await self._user_center.update_user_password(self._current_user_id, new_password)
        return (True, "") if success else (False, "密码更新失败")

    async def switch_account(self, username: str, password: str) -> tuple[bool, Optional[int]]:
        self._current_user_id = None
        return await self.login(username, password)

    async def get_current_user_profile(self) -> Optional[dict]:
        if self._current_user_id is None:
            return None
        return await self._user_center.get_user_by_id(self._current_user_id)

    async def update_username(self, new_username: str) -> bool:
        if self._current_user_id is None:
            return False
        return await self._user_center.update_username(self._current_user_id, new_username)

    async def list_user_resources(self) -> list[dict]:
        if self._current_user_id is None:
            return []
        return await self._user_center.get_resources_by_owner(self._current_user_id)
