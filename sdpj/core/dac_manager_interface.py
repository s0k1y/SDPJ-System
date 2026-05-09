"""DACManager 接口定义

被依赖模块: StateScheduler
"""

from typing import Protocol


class DACManagerInterface(Protocol):
    """自主访问控制管理接口"""

    async def grant_access(self, resource_id: int, target_username: str, caller_user_id: int) -> tuple[bool, str]:
        """授予其他用户对私有资源的读权限"""
        ...

    async def revoke_access(self, acl_id: int, caller_user_id: int) -> tuple[bool, str]:
        """移除已授予的读权限"""
        ...

    async def check_access(self, resource_id: int, user_id: int) -> bool:
        """判定用户对资源是否具备访问权"""
        ...

    async def get_access_list(self, resource_id: int, caller_user_id: int) -> tuple[bool, list[dict]]:
        """查询某资源的授权清单"""
        ...
