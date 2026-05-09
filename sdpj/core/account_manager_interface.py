"""AccountManager 接口定义

被依赖模块: StateScheduler
"""

from typing import Optional, Protocol


class AccountManagerInterface(Protocol):
    """用户账号管理接口"""

    async def register(self, username: str, password: str) -> tuple[bool, Optional[int], str]:
        """用户注册，返回 (成功标志, 用户ID或None, 消息)"""
        ...

    async def unregister(self, user_id: int) -> tuple[bool, str]:
        """用户注销"""
        ...

    async def login(self, username: str, password: str) -> tuple[bool, Optional[int], str]:
        """用户登录，返回 (成功标志, 用户ID或None, 消息)"""
        ...

    def get_current_session(self) -> Optional[int]:
        """获取当前登录用户ID"""
        ...

    def logout(self) -> bool:
        """用户登出"""
        ...

    async def switch_account(self, username: str, password: str) -> tuple[bool, Optional[int]]:
        """账号切换"""
        ...

    async def list_all_users(self) -> list[dict]:
        """获取所有用户列表"""
        ...

    async def get_profile_for_user(self, user_id: int) -> Optional[dict]:
        """通过用户ID查询用户资料"""
        ...

    async def change_password_for_user(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """修改指定用户密码"""
        ...

    async def update_username_for_user(self, user_id: int, new_username: str) -> bool:
        """更新指定用户名"""
        ...

    async def list_resources_for_user(self, user_id: int) -> list[dict]:
        """列出指定用户拥有的受控资源"""
        ...

    async def list_shared_resources_for_user(self, user_id: int) -> list[dict]:
        """列出分享给指定用户的受控资源"""
        ...
