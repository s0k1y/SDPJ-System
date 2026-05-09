"""DACManager 自主访问控制管理模块

依赖模块: UserCenter (via interface)
被依赖模块: StateScheduler
"""

from sdpj.drivers.user_center_interface import UserCenterInterface

from .dac_manager_interface import DACManagerInterface


class DACManager(DACManagerInterface):
    """自主访问控制管理"""

    def __init__(self, user_center: UserCenterInterface):
        self._user_center = user_center

    async def _get_resource_owner(self, resource_id: int) -> int | None:
        resource = await self._user_center.get_resource_by_id(resource_id)
        if resource is None:
            return None
        return resource.get("owner_user_id")

    async def grant_access(self, resource_id: int, target_username: str, caller_user_id: int) -> tuple[bool, str]:
        owner_id = await self._get_resource_owner(resource_id)
        if owner_id is None:
            return False, "资源不存在"
        if owner_id != caller_user_id:
            return False, "仅资源拥有者可授予访问权"
        target_user = await self._user_center.get_user_by_username(target_username)
        if target_user is None:
            return False, f"用户 '{target_username}' 不存在"
        target_user_id = target_user["user_id"]
        already = await self._user_center.check_access(resource_id, target_user_id)
        if already:
            return False, "该用户已拥有访问权"
        try:
            acl_id = await self._user_center.grant_access(resource_id, target_user_id)
            return True, str(acl_id)
        except ValueError as e:
            return False, str(e)

    async def revoke_access(self, acl_id: int, caller_user_id: int) -> tuple[bool, str]:
        target_acl = await self._user_center.get_acl_by_id(acl_id)
        if target_acl is None:
            return False, "访问控制项不存在"

        resource_id = target_acl.get("resource_id")
        owner_id = await self._get_resource_owner(resource_id)
        if owner_id != caller_user_id:
            return False, "仅资源拥有者可移除访问权"

        success = await self._user_center.revoke_access(acl_id)
        return (True, "") if success else (False, "移除失败")

    async def check_access(self, resource_id: int, user_id: int) -> bool:
        owner_id = await self._get_resource_owner(resource_id)
        if owner_id is None:
            return False
        if owner_id == user_id:
            return True
        return await self._user_center.check_access(resource_id, user_id)

    async def batch_check_accessible_resource_ids(self, user_id: int, resource_ids: list[int]) -> set[int]:
        """批量查询用户在指定资源中有访问权限的资源 ID 集合"""
        if not resource_ids:
            return set()
        return await self._user_center.get_accessible_resource_ids(user_id, resource_ids)

    async def get_access_list(self, resource_id: int, caller_user_id: int) -> tuple[bool, list[dict]]:
        owner_id = await self._get_resource_owner(resource_id)
        if owner_id is None:
            return False, []
        if owner_id != caller_user_id:
            return False, []
        acl_list = await self._user_center.get_access_list(resource_id)
        return True, acl_list
