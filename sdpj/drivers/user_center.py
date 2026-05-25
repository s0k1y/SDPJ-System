"""UserCenter 用户管理中心实现

负责用户账号生命周期、凭据校验、资源登记与查询、ACL 授权管理、私有检测配置内容管理。
依赖：UserDB, UtilsLib
"""

from typing import Optional, cast

from sdpj.infrastructure.database.user_db.interface import UserDBInterface


class UserCenter:
    """用户管理中心实现类"""

    def __init__(self, user_db: UserDBInterface):
        self._user_db = user_db

    # ==================== 账号生命周期 ====================

    async def register_user(self, username: str, password: str) -> int:
        """注册新用户

        Args:
            username: 账号
            password: 明文密码

        Returns:
            新用户的用户 ID

        Raises:
            ValueError: 账号已存在时拒绝注册
        """
        user_id = await self._user_db.create_user(username, password)
        return user_id

    async def delete_user(self, user_id: int) -> bool:
        """注销用户

        Args:
            user_id: 用户 ID

        Returns:
            注销结果（True 表示成功）
        """
        return await self._user_db.delete_user(user_id)

    async def update_username(self, user_id: int, new_username: str) -> bool:
        return await self._user_db.update_username(user_id, new_username)

    async def update_user_password(self, user_id: int, new_password: str) -> bool:
        """修改用户密码

        Args:
            user_id: 用户 ID
            new_password: 新明文密码

        Returns:
            修改结果（True 表示成功）

        Raises:
            ValueError: 用户 ID 不存在时抛出
        """
        return await self._user_db.update_user_password(user_id, new_password)

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """按账号查询用户信息

        Args:
            username: 账号

        Returns:
            用户信息字典（不含存储密码），不存在时返回 None
        """
        user = await self._user_db.get_user_by_username(username)

        if user is None:
            return None

        # 移除敏感字段（存储密码）
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """按用户 ID 查询用户信息

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典（不含存储密码），不存在时返回 None
        """
        user = await self._user_db.get_user_by_id(user_id)

        if user is None:
            return None

        # 移除敏感字段（存储密码）
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }

    # ==================== 凭据校验 ====================

    async def verify_credentials(
        self, username: str, password: str
    ) -> tuple[bool, Optional[int], str]:
        """登录凭据校验

        Args:
            username: 账号
            password: 明文密码

        Returns:
            (是否成功, 用户ID, 错误消息)
        """
        # 查询用户信息（含存储密码）
        user = await self._user_db.get_user_by_username(username)

        if user is None:
            return False, None, "账号未注册，请先注册"

        if user["password"] == password:
            return True, user["user_id"], ""

        return False, None, "密码错误"

    async def get_all_users(self) -> list[dict]:
        """获取所有用户列表

        Returns:
            用户列表，每个用户包含 user_id, username, created_at
        """
        users = await self._user_db.get_all_users()
        return [
            {
                "user_id": u["user_id"],
                "username": u["username"],
                "created_at": u.get("created_at", "-"),
            }
            for u in users
        ]

    # ==================== 资源登记与查询 ====================

    async def register_resource(self, resource_type: str, owner_user_id: int) -> int:
        """登记受控资源

        Args:
            resource_type: 资源类型
            owner_user_id: 拥有者用户 ID

        Returns:
            新创建资源的资源 ID

        Raises:
            ValueError: 拥有者用户 ID 不存在时拒绝写入
        """
        return await self._user_db.register_resource(resource_type, owner_user_id)

    async def delete_resource(self, resource_id: int) -> bool:
        """移除受控资源

        Args:
            resource_id: 资源 ID

        Returns:
            移除结果（True 表示成功）
        """
        return await self._user_db.delete_resource(resource_id)

    async def get_resources_by_owner(self, user_id: int) -> list[dict]:
        """按拥有者查询资源清单

        Args:
            user_id: 用户 ID

        Returns:
            该用户拥有的全部资源列表
        """
        return await self._user_db.get_resources_by_owner(user_id)

    async def get_resources_shared_with(self, user_id: int) -> list[dict]:
        """按被授权用户查询被共享的资源清单"""
        return await self._user_db.get_resources_shared_with(user_id)

    async def get_resource_by_id(self, resource_id: int) -> Optional[dict]:
        """按 ID 查询资源

        Args:
            resource_id: 资源 ID

        Returns:
            资源信息字典，不存在时返回 None
        """
        return await self._user_db.get_resource_by_id(resource_id)

    # ==================== ACL 授权管理 ====================

    async def grant_access(self, resource_id: int, grantee_user_id: int) -> int:
        """授予他人访问权

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            新创建的访问控制项 ID

        Raises:
            ValueError: 资源 ID 或被授权用户 ID 不存在时拒绝写入
        """
        return await self._user_db.add_access_control(resource_id, grantee_user_id)

    async def revoke_access(self, acl_id: int) -> bool:
        """移除已授予的访问权

        Args:
            acl_id: 访问控制项 ID

        Returns:
            移除结果（True 表示成功）
        """
        return await self._user_db.delete_access_control(acl_id)

    async def get_access_list(self, resource_id: int) -> list[dict]:
        """查询某资源的授权清单

        Args:
            resource_id: 资源 ID

        Returns:
            该资源下全部访问控制项列表
        """
        return await self._user_db.get_access_controls_by_resource(resource_id)

    async def check_access(self, resource_id: int, user_id: int) -> bool:
        return await self._user_db.check_access_control_exists(resource_id, user_id)

    async def get_accessible_resource_ids(self, user_id: int, resource_ids: list[int]) -> set[int]:
        return cast(set[int], await self._user_db.get_accessible_resource_ids(user_id, resource_ids))

    async def get_acl_by_id(self, acl_id: int):
        return await self._user_db.get_access_control_by_id(acl_id)

    # ==================== 私有检测配置内容管理 ====================

    async def write_private_config(self, config_id: int, config_content: dict) -> bool:
        """写入用户私有检测配置内容

        Args:
            config_id: 配置 ID（等同于其对应资源的资源 ID）
            config_content: 配置内容 JSON

        Returns:
            写入结果（True 表示成功）

        Raises:
            ValueError: 对应资源 ID 不存在时拒绝写入
            ValueError: 同配置 ID 已有内容时拒绝（覆盖请用更新）
        """
        return await self._user_db.write_private_config(config_id, config_content)

    async def read_private_config(self, config_id: int) -> Optional[dict]:
        """读取用户私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            配置内容 JSON，不存在时返回 None
        """
        return await self._user_db.read_private_config(config_id)

    async def read_private_configs_batch(self, config_ids: list[int]) -> dict[int, dict]:
        """批量读取用户私有检测配置内容

        Args:
            config_ids: 配置 ID 列表

        Returns:
            {config_id: config_content_dict} 映射
        """
        return cast(dict[int, dict], await self._user_db.read_private_configs_batch(config_ids))

    async def update_private_config(self, config_id: int, config_content: dict) -> bool:
        """更新用户私有检测配置内容

        Args:
            config_id: 配置 ID
            config_content: 新配置内容 JSON

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 配置 ID 不存在时拒绝更新
        """
        return await self._user_db.update_private_config(config_id, config_content)

    async def delete_private_config(self, config_id: int) -> bool:
        """清除用户私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            清除结果（True 表示成功）
        """
        return await self._user_db.delete_private_config(config_id)
