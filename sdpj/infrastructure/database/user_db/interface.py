"""UserDB 接口定义

UserDB 模块对外暴露的接口契约，定义用户信息数据库的所有能力。
UserCenter 是唯一调用方。
"""

from typing import Protocol, Optional
from datetime import datetime


class UserDBInterface(Protocol):
    """用户信息数据库接口

    职责范围：
    - 用户账号级能力：创建、删除、更新、查询用户
    - 资源级能力：登记、删除、查询资源
    - 访问控制列表级能力：添加、删除、查询、判定访问控制项
    - 私有检测配置内容级能力：写入、读取、更新、删除配置内容

    不负责的边界：
    - 不做密码加密/哈希处理（由 UserCenter 借助 UtilsLib 完成）
    - 不做账号格式与密码强度校验（由调用方完成）
    - 不维护用户登录会话与在线态
    - 不做权限授予资格的业务判定（由 DACManager 完成）
    - 不解析配置内容的业务语义
    """

    # ==================== 用户账号级能力 ====================

    async def create_user(self, username: str, password: str) -> int:
        """创建用户

        Args:
            username: 账号
            password: 密码

        Returns:
            新创建用户的用户 ID

        Raises:
            ValueError: 账号在系统内重复时拒绝写入
        """
        ...

    async def delete_user(self, user_id: int) -> bool:
        """删除用户

        后置条件：
        - 级联删除该用户拥有的资源记录及其相关 ACL 项（作为拥有者）
        - 清理该用户作为被授权者出现在他人资源 ACL 中的所有条目

        Args:
            user_id: 用户 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...

    async def update_user_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码

        Args:
            user_id: 用户 ID
            new_password: 新密码

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 用户 ID 不存在时抛出
        """
        ...

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """按账号查询用户

        Args:
            username: 账号

        Returns:
            用户信息字典，包含：
            - user_id: 用户 ID
            - username: 账号
            - password: 已存储密码
            - created_at: 创建时间
            不存在时返回 None
        """
        ...

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """按 ID 查询用户

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典，包含：
            - user_id: 用户 ID
            - username: 账号
            - password: 已存储密码
            - created_at: 创建时间
            不存在时返回 None
        """
        ...

    async def update_username(self, user_id: int, new_username: str) -> bool:
        """更新用户名

        Args:
            user_id: 用户 ID
            new_username: 新用户名

        Returns:
            更新结果（True 表示成功）
        """
        ...

    async def get_all_users(self) -> list[dict]:
        """获取所有用户列表

        Returns:
            所有用户信息列表，每条包含：
            - user_id: 用户 ID
            - username: 账号
            - password: 已存储密码
            - created_at: 创建时间
        """
        ...

    # ==================== 资源级能力 ====================

    async def register_resource(self, resource_type: str, owner_user_id: int) -> int:
        """登记资源

        Args:
            resource_type: 资源类型
            owner_user_id: 资源拥有者用户 ID

        Returns:
            新创建资源的资源 ID

        Raises:
            ValueError: 资源拥有者用户 ID 不存在时拒绝写入
        """
        ...

    async def delete_resource(self, resource_id: int) -> bool:
        """删除资源

        后置条件：
        - 级联删除该资源相关的全部访问控制项
        - 若该资源在私有检测配置内容表中有对应条目，一并级联清理

        Args:
            resource_id: 资源 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...

    async def get_resources_by_owner(self, user_id: int) -> list[dict]:
        """按拥有者查询资源列表

        Args:
            user_id: 用户 ID

        Returns:
            该用户拥有的全部资源列表，每条包含：
            - resource_id: 资源 ID
            - resource_type: 资源类型
            - owner_user_id: 拥有者用户 ID
            - created_at: 创建时间
        """
        ...

    async def get_resources_shared_with(self, user_id: int) -> list[dict]:
        """按被授权用户查询被共享的资源列表

        Args:
            user_id: 被授权用户 ID

        Returns:
            该用户被授权访问的全部资源列表，每条包含：
            - resource_id: 资源 ID
            - resource_type: 资源类型
            - owner_user_id: 拥有者用户 ID
            - created_at: 创建时间
        """
        ...

    async def get_resource_by_id(self, resource_id: int) -> Optional[dict]:
        """按 ID 查询资源

        Args:
            resource_id: 资源 ID

        Returns:
            资源信息字典，包含：
            - resource_id: 资源 ID
            - resource_type: 资源类型
            - owner_user_id: 拥有者用户 ID
            - created_at: 创建时间
            不存在时返回 None
        """
        ...

    # ==================== 访问控制列表级能力 ====================

    async def add_access_control(self, resource_id: int, grantee_user_id: int) -> int:
        """添加访问控制项

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            新创建的访问控制项 ID（若已存在则幂等返回现有 ID）

        Raises:
            ValueError: 资源 ID 或被授权用户 ID 不存在时拒绝写入
        """
        ...

    async def delete_access_control(self, acl_id: int) -> bool:
        """删除访问控制项

        Args:
            acl_id: 访问控制项 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...

    async def get_access_controls_by_resource(self, resource_id: int) -> list[dict]:
        """按资源 ID 查询访问控制项列表

        Args:
            resource_id: 资源 ID

        Returns:
            该资源下全部访问控制项列表，每条包含：
            - acl_id: 访问控制项 ID
            - resource_id: 资源 ID
            - grantee_user_id: 被授权用户 ID
            - created_at: 创建时间
        """
        ...

    async def get_access_control_by_id(self, acl_id: int) -> Optional[dict]:
        """按 ID 查询单条访问控制项

        Args:
            acl_id: 访问控制项 ID

        Returns:
            访问控制项字典，包含：
            - acl_id: 访问控制项 ID
            - resource_id: 资源 ID
            - grantee_user_id: 被授权用户 ID
            - created_at: 创建时间
            不存在时返回 None
        """
        ...

    async def check_access_control_exists(self, resource_id: int, grantee_user_id: int) -> bool:
        """判定访问控制项是否存在

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            对应授权项是否存在的布尔判定
        """
        ...

    # ==================== 私有检测配置内容级能力 ====================

    async def write_private_config(self, config_id: int, config_content: dict) -> bool:
        """写入私有检测配置内容

        Args:
            config_id: 配置 ID（等同于其对应资源的资源 ID）
            config_content: 配置内容 JSON

        Returns:
            写入结果（True 表示成功）

        Raises:
            ValueError: 对应资源 ID 不存在时拒绝写入
            ValueError: 同配置 ID 已有内容时拒绝（覆盖请用更新）
        """
        ...

    async def read_private_config(self, config_id: int) -> Optional[dict]:
        """按 ID 读取私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            对应配置内容 JSON，不存在时返回 None
        """
        ...

    async def update_private_config(self, config_id: int, config_content: dict) -> bool:
        """更新私有检测配置内容

        Args:
            config_id: 配置 ID
            config_content: 新配置内容 JSON

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 配置 ID 不存在时拒绝更新
        """
        ...

    async def delete_private_config(self, config_id: int) -> bool:
        """删除私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...
