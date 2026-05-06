"""AccountManager 接口定义

被依赖模块: StateScheduler
"""
from typing import Protocol, Optional


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

    async def change_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        """修改当前用户密码"""
        ...

    async def switch_account(self, username: str, password: str) -> tuple[bool, Optional[int]]:
        """账号切换"""
        ...

    async def get_current_user_profile(self) -> Optional[dict]:
        """查询当前用户资料"""
        ...

    async def update_username(self, new_username: str) -> bool:
        """更新当前用户名"""
        ...

    async def list_user_resources(self) -> list[dict]:
        """列出当前用户拥有的受控资源"""
        ...

    async def list_all_users(self) -> list[dict]:
        """获取所有用户列表"""
        ...
