"""UserCenter 接口定义

UserCenter 模块对外暴露的接口契约，定义用户管理中心的所有能力。
调用方：PrivateConfigManager, ReportManager, AccountManager, DACManager
"""

from typing import Protocol, Optional


class UserCenterInterface(Protocol):
    """用户管理中心接口

    职责范围：
    - 账号生命周期：注册、注销、修改密码、查询用户信息
    - 凭据校验：登录凭据校验
    - 资源登记与查询：登记、移除、查询受控资源
    - ACL 授权管理：授予、移除、查询、判定访问权
    - 私有检测配置内容管理：写入、读取、更新、清除配置内容

    不负责的边界：
    - 不维护用户登录会话与在线态
    - 不做账号格式/密码强度校验（由 AccountManager 完成）
    - 不持有或管理加解密密钥的生命周期
    - 不做权限授予资格的业务判定（由 DACManager 完成）
    - 不维护受控资源的具体内容（仅维护元信息与 ACL）
    - 不向上透出存储密码等敏感字段
    """

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

        后置条件:
            用户记录已持久化，存储密码为不可逆摘要形式

        触发场景:
            用户注册（对应 1.spec.md 功能 3.1.1.1）
        """
        ...

    async def delete_user(self, user_id: int) -> bool:
        """注销用户

        Args:
            user_id: 用户 ID

        Returns:
            注销结果（True 表示成功）

        后置条件:
            该用户及其拥有的资源、相关 ACL 条目全部清理（由下层级联）

        触发场景:
            用户注销账号（对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def update_user_password(self, user_id: int, new_password: str) -> bool:
        """修改用户密码

        Args:
            user_id: 用户 ID
            new_password: 新明文密码

        Returns:
            修改结果（True 表示成功）

        Raises:
            ValueError: 用户 ID 不存在时抛出

        后置条件:
            存储密码已更新为新密码的不可逆摘要

        触发场景:
            用户修改密码（对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """按账号查询用户信息

        Args:
            username: 账号

        Returns:
            用户信息字典，包含：
            - user_id: 用户 ID
            - username: 账号
            - created_at: 创建时间
            不存在时返回 None

        注意:
            不向上透出存储密码

        触发场景:
            账号切换（对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """按用户 ID 查询用户信息

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典，包含：
            - user_id: 用户 ID
            - username: 账号
            - created_at: 创建时间
            不存在时返回 None

        注意:
            不向上透出存储密码

        触发场景:
            - AccountManager 读取当前用户信息、账号切换（对应 1.spec.md 功能 3.1.1.2）
            - ReportManager 查询报告归属用户（对应 1.spec.md 功能 1.5 / 1.6）
        """
        ...

    # ==================== 凭据校验 ====================

    async def verify_credentials(self, username: str, password: str) -> Optional[int]:
        """登录凭据校验

        Args:
            username: 账号
            password: 明文密码

        Returns:
            校验通过时返回用户 ID，失败时返回 None

        触发场景:
            用户登录（对应 1.spec.md 功能 3.1.1.1）

        不负责的边界:
            不建立、不维护登录会话与在线态
        """
        ...

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

        触发场景:
            用户创建受控资源（如私有检测配置文件、私有数据集等）时为其建立 ACL 承载点
            （对应 1.spec.md 功能 3.1.1.2）

        不负责的边界:
            不维护资源实体的具体内容（仅维护元信息与 ACL）
        """
        ...

    async def delete_resource(self, resource_id: int) -> bool:
        """移除受控资源

        Args:
            resource_id: 资源 ID

        Returns:
            移除结果（True 表示成功）

        后置条件:
            该资源相关全部 ACL 条目、若有对应私有检测配置内容均由下层级联清理

        触发场景:
            用户删除受控资源（对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def get_resources_by_owner(self, user_id: int) -> list[dict]:
        """按拥有者查询资源清单

        Args:
            user_id: 用户 ID

        Returns:
            该用户拥有的全部资源列表，每条包含：
            - resource_id: 资源 ID
            - resource_type: 资源类型
            - owner_user_id: 拥有者用户 ID
            - created_at: 创建时间

        触发场景:
            AccountManager 列出当前用户的受控资产（对应 1.spec.md 功能 3.1.1.2）
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

        触发场景:
            DACManager 在权限判定前定位资源归属（对应 1.spec.md 功能 3.1.2）
        """
        ...

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

        触发场景:
            资源拥有者对其他用户授予访问权（对应 1.spec.md 功能 3.1.2）

        不负责的边界:
            不判定调用者是否具备「授权他人」资格（由 DACManager 在调用前完成）
        """
        ...

    async def revoke_access(self, acl_id: int) -> bool:
        """移除已授予的访问权

        Args:
            acl_id: 访问控制项 ID

        Returns:
            移除结果（True 表示成功）

        触发场景:
            资源拥有者收回对他人的授权（对应 1.spec.md 功能 3.1.2）
        """
        ...

    async def get_access_list(self, resource_id: int) -> list[dict]:
        """查询某资源的授权清单

        Args:
            resource_id: 资源 ID

        Returns:
            该资源下全部访问控制项列表，每条包含：
            - acl_id: 访问控制项 ID
            - resource_id: 资源 ID
            - grantee_user_id: 被授权用户 ID
            - created_at: 创建时间

        触发场景:
            DACManager 展示资源授权状况（对应 1.spec.md 功能 3.1.2）
        """
        ...

    async def check_access(self, resource_id: int, user_id: int) -> bool:
        """判定用户对资源是否具备访问权

        Args:
            resource_id: 资源 ID
            user_id: 用户 ID

        Returns:
            是否具备访问权的布尔判定

        触发场景:
            DACManager 校验某用户对某资源的访问权（对应 1.spec.md 功能 3.1.2）
        """
        ...

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

        触发场景:
            PrivateConfigManager 在创建私有检测配置后持久化其内容
            （对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def read_private_config(self, config_id: int) -> Optional[dict]:
        """读取用户私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            配置内容 JSON，不存在时返回 None

        触发场景:
            PrivateConfigManager 在用户查看或系统加载私有检测配置时
            （对应 1.spec.md 功能 1.1 / 1.2 / 1.3 / 3.1.1.2）
        """
        ...

    async def update_private_config(self, config_id: int, config_content: dict) -> bool:
        """更新用户私有检测配置内容

        Args:
            config_id: 配置 ID
            config_content: 新配置内容 JSON

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 配置 ID 不存在时拒绝更新

        触发场景:
            PrivateConfigManager 在用户编辑已有私有配置后写入新内容
            （对应 1.spec.md 功能 3.1.1.2）
        """
        ...

    async def delete_private_config(self, config_id: int) -> bool:
        """清除用户私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            清除结果（True 表示成功）

        触发场景:
            作为显式清除路径，通常由资源删除级联完成
            （对应 1.spec.md 功能 3.1.1.2）
        """
        ...
