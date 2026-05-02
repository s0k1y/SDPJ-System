"""DACManager 接口定义"""
from typing import Protocol


class DACManagerInterface(Protocol):
    """自主访问控制管理接口"""

    async def init(self) -> None:
        """初始化DAC管理器"""
        ...

    async def grant_access(self, user_id: int, resource_id: int, permission: str) -> bool:
        """授予访问权限

        Args:
            user_id: 用户ID
            resource_id: 资源ID
            permission: 权限类型

        Returns:
            授予成功返回True
        """
        ...

    async def revoke_access(self, user_id: int, resource_id: int) -> bool:
        """撤销访问权限

        Args:
            user_id: 用户ID
            resource_id: 资源ID

        Returns:
            撤销成功返回True
        """
        ...

    async def check_access(self, user_id: int, resource_id: int, permission: str) -> bool:
        """检查访问权限

        Args:
            user_id: 用户ID
            resource_id: 资源ID
            permission: 权限类型

        Returns:
            有权限返回True
        """
        ...
