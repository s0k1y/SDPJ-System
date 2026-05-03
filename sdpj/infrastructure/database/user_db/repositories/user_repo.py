"""用户仓储层

负责用户表的 CRUD 操作。
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import User


class UserRepository:
    """用户仓储

    职责：
    - 创建用户
    - 删除用户
    - 更新用户密码
    - 按账号查询用户
    - 按 ID 查询用户
    """

    def __init__(self, session: AsyncSession):
        """初始化用户仓储

        Args:
            session: 数据库会话
        """
        self._session = session

    async def create(self, username: str, password: str) -> User:
        """创建用户

        Args:
            username: 账号
            password: 密码

        Returns:
            新创建的用户对象

        Raises:
            ValueError: 账号重复时抛出
        """
        user = User(username=username, password=password)
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ValueError(f"用户名 '{username}' 已存在") from e
        return user

    async def delete(self, user_id: int) -> bool:
        """删除用户

        Args:
            user_id: 用户 ID

        Returns:
            删除结果（True 表示成功）
        """
        stmt = delete(User).where(User.user_id == user_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码

        Args:
            user_id: 用户 ID
            new_password: 新密码

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 用户不存在时抛出
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")

        user.password = new_password
        await self._session.flush()
        return True

    async def update_username(self, user_id: int, new_username: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户 ID {user_id} 不存在")
        user.username = new_username
        await self._session.flush()
        return True

    async def get_by_username(self, username: str) -> Optional[User]:
        """按账号查询用户

        Args:
            username: 账号

        Returns:
            用户对象，不存在时返回 None
        """
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """按 ID 查询用户

        Args:
            user_id: 用户 ID

        Returns:
            用户对象，不存在时返回 None
        """
        stmt = select(User).where(User.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
