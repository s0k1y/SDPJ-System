"""UserDB 实现

整合所有仓储层，实现 UserDBInterface 接口。
"""

from typing import Optional

from .interface import UserDBInterface
from .session import UserDBSessionManager
from .repositories import (
    UserRepository,
    ResourceRepository,
    ACLRepository,
    PrivateConfigRepository,
)


class UserDB:
    """用户信息数据库实现

    职责：
    - 实现 UserDBInterface 定义的所有能力
    - 协调各仓储层完成数据库操作
    - 管理事务边界
    """

    def __init__(self, session_manager: UserDBSessionManager):
        """初始化 UserDB

        Args:
            session_manager: 会话管理器
        """
        self._session_manager = session_manager

    # ==================== 用户账号级能力 ====================

    async def create_user(self, username: str, password: str) -> int:
        """创建用户"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.create(username, password)
            return user.user_id

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            return await user_repo.delete(user_id)

    async def update_user_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            return await user_repo.update_password(user_id, new_password)

    async def update_username(self, user_id: int, new_username: str) -> bool:
        """更新用户名"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            return await user_repo.update_username(user_id, new_username)

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """按 ID 查询用户"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            if not user:
                return None
            return {
                "user_id": user.user_id,
                "username": user.username,
                "password": user.password,
                "created_at": user.created_at,
            }

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """按账号查询用户"""
        async with self._session_manager.session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_username(username)
            if not user:
                return None
            return {
                "user_id": user.user_id,
                "username": user.username,
                "password": user.password,
                "created_at": user.created_at,
            }

    # ==================== 资源级能力 ====================

    async def register_resource(self, resource_type: str, owner_user_id: int) -> int:
        """登记资源"""
        async with self._session_manager.session() as session:
            resource_repo = ResourceRepository(session)
            resource = await resource_repo.create(resource_type, owner_user_id)
            return resource.resource_id

    async def delete_resource(self, resource_id: int) -> bool:
        """删除资源"""
        async with self._session_manager.session() as session:
            resource_repo = ResourceRepository(session)
            return await resource_repo.delete(resource_id)

    async def get_resources_by_owner(self, user_id: int) -> list[dict]:
        """按拥有者查询资源列表"""
        async with self._session_manager.session() as session:
            resource_repo = ResourceRepository(session)
            resources = await resource_repo.get_by_owner(user_id)
            return [
                {
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "owner_user_id": r.owner_user_id,
                    "created_at": r.created_at,
                }
                for r in resources
            ]

    async def get_resource_by_id(self, resource_id: int) -> Optional[dict]:
        """按 ID 查询资源"""
        async with self._session_manager.session() as session:
            resource_repo = ResourceRepository(session)
            resource = await resource_repo.get_by_id(resource_id)
            if not resource:
                return None
            return {
                "resource_id": resource.resource_id,
                "resource_type": resource.resource_type,
                "owner_user_id": resource.owner_user_id,
                "created_at": resource.created_at,
            }

    # ==================== 访问控制列表级能力 ====================

    async def add_access_control(self, resource_id: int, grantee_user_id: int) -> int:
        """添加访问控制项"""
        async with self._session_manager.session() as session:
            acl_repo = ACLRepository(session)
            acl = await acl_repo.create(resource_id, grantee_user_id)
            return acl.acl_id

    async def delete_access_control(self, acl_id: int) -> bool:
        """删除访问控制项"""
        async with self._session_manager.session() as session:
            acl_repo = ACLRepository(session)
            return await acl_repo.delete(acl_id)

    async def get_access_controls_by_resource(self, resource_id: int) -> list[dict]:
        """按资源 ID 查询访问控制项列表"""
        async with self._session_manager.session() as session:
            acl_repo = ACLRepository(session)
            acls = await acl_repo.get_by_resource(resource_id)
            return [
                {
                    "acl_id": acl.acl_id,
                    "resource_id": acl.resource_id,
                    "grantee_user_id": acl.grantee_user_id,
                    "created_at": acl.created_at,
                }
                for acl in acls
            ]

    async def get_access_control_by_id(self, acl_id: int) -> Optional[dict]:
        async with self._session_manager.session() as session:
            acl_repo = ACLRepository(session)
            acl = await acl_repo.get_by_id(acl_id)
            if acl is None:
                return None
            return {
                "acl_id": acl.acl_id,
                "resource_id": acl.resource_id,
                "grantee_user_id": acl.grantee_user_id,
                "created_at": acl.created_at,
            }

    async def check_access_control_exists(self, resource_id: int, grantee_user_id: int) -> bool:
        """判定访问控制项是否存在"""
        async with self._session_manager.session() as session:
            acl_repo = ACLRepository(session)
            return await acl_repo.exists(resource_id, grantee_user_id)

    # ==================== 私有检测配置内容级能力 ====================

    async def write_private_config(self, config_id: int, config_content: dict) -> bool:
        """写入私有检测配置内容"""
        async with self._session_manager.session() as session:
            config_repo = PrivateConfigRepository(session)
            await config_repo.create(config_id, config_content)
            return True

    async def read_private_config(self, config_id: int) -> Optional[dict]:
        """按 ID 读取私有检测配置内容"""
        async with self._session_manager.session() as session:
            config_repo = PrivateConfigRepository(session)
            return await config_repo.get_by_id(config_id)

    async def update_private_config(self, config_id: int, config_content: dict) -> bool:
        """更新私有检测配置内容"""
        async with self._session_manager.session() as session:
            config_repo = PrivateConfigRepository(session)
            return await config_repo.update(config_id, config_content)

    async def delete_private_config(self, config_id: int) -> bool:
        """删除私有检测配置内容"""
        async with self._session_manager.session() as session:
            config_repo = PrivateConfigRepository(session)
            return await config_repo.delete(config_id)
