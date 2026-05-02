"""DACManager 自主访问控制管理模块"""
from sdpj.drivers.user_center import UserCenter


class DACManager:
    """自主访问控制管理"""

    def __init__(self):
        self.user_center = UserCenter()
        self._initialized = False

    async def init(self):
        if not self._initialized:
            await self.user_center.init()
            self._initialized = True

    async def grant_access(self, resource_id: int, owner_id: int, target_user_id: int) -> tuple[bool, str]:
        return True, "授权成功"

    async def revoke_access(self, acl_id: int, owner_id: int) -> tuple[bool, str]:
        return True, "移除成功"

    async def check_access(self, user_id: int, resource_id: int) -> bool:
        return await self.user_center.check_access(user_id, resource_id)
