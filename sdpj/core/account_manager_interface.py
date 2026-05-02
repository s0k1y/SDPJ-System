"""AccountManager 接口定义"""
from typing import Protocol


class AccountManagerInterface(Protocol):
    """用户账号管理接口"""

    async def init(self) -> None:
        """初始化账号管理器"""
        ...

    async def register(self, username: str, password: str) -> tuple[bool, str]:
        """注册新用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            (成功标志, 消息)
        """
        ...

    async def login(self, username: str, password: str) -> tuple[bool, str | None]:
        """用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (成功标志, 会话ID)
        """
        ...

    def logout(self, session_id: str) -> bool:
        """用户登出

        Args:
            session_id: 会话ID

        Returns:
            成功返回True
        """
        ...
