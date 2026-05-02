"""资源仓储层

负责资源表的 CRUD 操作。
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import Resource


class ResourceRepository:
    """资源仓储

    职责：
    - 登记资源
    - 删除资源
    - 按拥有者查询资源列表
    - 按 ID 查询资源
    """

    def __init__(self, session: AsyncSession):
        """初始化资源仓储

        Args:
            session: 数据库会话
        """
        self._session = session

    async def create(self, resource_type: str, owner_user_id: int) -> Resource:
        """登记资源

        Args:
            resource_type: 资源类型
            owner_user_id: 资源拥有者用户 ID

        Returns:
            新创建的资源对象

        Raises:
            ValueError: 拥有者用户 ID 不存在时抛出
        """
        resource = Resource(resource_type=resource_type, owner_user_id=owner_user_id)
        self._session.add(resource)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ValueError(f"用户 ID {owner_user_id} 不存在") from e
        return resource

    async def delete(self, resource_id: int) -> bool:
        """删除资源

        Args:
            resource_id: 资源 ID

        Returns:
            删除结果（True 表示成功）
        """
        stmt = delete(Resource).where(Resource.resource_id == resource_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def get_by_owner(self, user_id: int) -> list[Resource]:
        """按拥有者查询资源列表

        Args:
            user_id: 用户 ID

        Returns:
            该用户拥有的全部资源列表
        """
        stmt = select(Resource).where(Resource.owner_user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, resource_id: int) -> Optional[Resource]:
        """按 ID 查询资源

        Args:
            resource_id: 资源 ID

        Returns:
            资源对象，不存在时返回 None
        """
        stmt = select(Resource).where(Resource.resource_id == resource_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
