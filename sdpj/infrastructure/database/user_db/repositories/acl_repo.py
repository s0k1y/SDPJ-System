"""访问控制列表仓储层

负责访问控制表的 CRUD 操作。
"""

from typing import Optional
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import AccessControl


class ACLRepository:
    """访问控制列表仓储

    职责：
    - 添加访问控制项
    - 删除访问控制项
    - 按资源 ID 查询访问控制项列表
    - 判定访问控制项是否存在
    """

    def __init__(self, session: AsyncSession):
        """初始化访问控制列表仓储

        Args:
            session: 数据库会话
        """
        self._session = session

    async def create(self, resource_id: int, grantee_user_id: int) -> AccessControl:
        """添加访问控制项

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            新创建的访问控制项对象（若已存在则返回现有对象）

        Raises:
            ValueError: 资源 ID 或被授权用户 ID 不存在时抛出
        """
        # 先检查是否已存在
        existing = await self.get_by_resource_and_grantee(resource_id, grantee_user_id)
        if existing:
            return existing

        acl = AccessControl(resource_id=resource_id, grantee_user_id=grantee_user_id)
        self._session.add(acl)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ValueError(f"资源 ID {resource_id} 或用户 ID {grantee_user_id} 不存在") from e
        return acl

    async def delete(self, acl_id: int) -> bool:
        """删除访问控制项

        Args:
            acl_id: 访问控制项 ID

        Returns:
            删除结果（True 表示成功）
        """
        stmt = delete(AccessControl).where(AccessControl.acl_id == acl_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def get_by_resource(self, resource_id: int) -> list[AccessControl]:
        """按资源 ID 查询访问控制项列表

        Args:
            resource_id: 资源 ID

        Returns:
            该资源下全部访问控制项列表
        """
        stmt = select(AccessControl).options(joinedload(AccessControl.grantee)).where(AccessControl.resource_id == resource_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_resource_and_grantee(
        self, resource_id: int, grantee_user_id: int
    ) -> Optional[AccessControl]:
        """按资源 ID 和被授权用户 ID 查询访问控制项

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            访问控制项对象，不存在时返回 None
        """
        stmt = select(AccessControl).where(
            and_(
                AccessControl.resource_id == resource_id,
                AccessControl.grantee_user_id == grantee_user_id
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_grantee(self, grantee_user_id: int) -> list[AccessControl]:
        """按被授权用户 ID 查询所有访问控制项（含关联资源）

        Args:
            grantee_user_id: 被授权用户 ID

        Returns:
            该用户被授权的全部访问控制项列表
        """
        stmt = (
            select(AccessControl)
            .options(joinedload(AccessControl.resource))
            .where(AccessControl.grantee_user_id == grantee_user_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_id(self, acl_id: int) -> Optional[AccessControl]:
        stmt = select(AccessControl).where(AccessControl.acl_id == acl_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, resource_id: int, grantee_user_id: int) -> bool:
        """判定访问控制项是否存在

        Args:
            resource_id: 资源 ID
            grantee_user_id: 被授权用户 ID

        Returns:
            对应授权项是否存在的布尔判定
        """
        acl = await self.get_by_resource_and_grantee(resource_id, grantee_user_id)
        return acl is not None

    async def get_accessible_resource_ids(self, user_id: int, resource_ids: list[int]) -> set[int]:
        """批量查询用户在指定资源中有访问权限的资源 ID 集合

        拥有者自动有权限，此外检查 ACL 表
        
        Args:
            user_id: 用户 ID
            resource_ids: 待检查的资源 ID 列表

        Returns:
            用户有访问权限的资源 ID 集合
        """
        if not resource_ids:
            return set()
        from ..models import Resource
        owner_stmt = select(Resource.resource_id).where(
            Resource.resource_id.in_(resource_ids),
            Resource.owner_user_id == user_id,
        )
        owner_result = await self._session.execute(owner_stmt)
        accessible = {row[0] for row in owner_result.all()}
        remaining = [rid for rid in resource_ids if rid not in accessible]
        if remaining:
            acl_stmt = select(AccessControl.resource_id).where(
                AccessControl.resource_id.in_(remaining),
                AccessControl.grantee_user_id == user_id,
            )
            acl_result = await self._session.execute(acl_stmt)
            accessible.update(row[0] for row in acl_result.all())
        return accessible
