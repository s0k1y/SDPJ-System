"""TaskGroup 仓储层

提供检测任务组的数据访问操作。
"""

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import TaskGroup


class TaskGroupRepository:
    """检测任务组仓储"""

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(self, user_id: int, model_id: str) -> TaskGroup:
        task_group_id = f"tg_{uuid.uuid4().hex[:16]}"
        task_group = TaskGroup(
            task_group_id=task_group_id,
            user_id=user_id,
            model_id=model_id
        )
        self.session.add(task_group)
        await self.session.flush()
        return task_group

    async def create_with_id(self, task_group_id: str, user_id: int, model_id: str) -> TaskGroup:
        task_group = TaskGroup(
            task_group_id=task_group_id,
            user_id=user_id,
            model_id=model_id
        )
        self.session.add(task_group)
        await self.session.flush()
        return task_group

    async def get_by_id(self, task_group_id: str) -> Optional[TaskGroup]:
        """按ID查询任务组

        Args:
            task_group_id: 任务组ID

        Returns:
            任务组对象，不存在时返回None
        """
        stmt = select(TaskGroup).where(TaskGroup.task_group_id == task_group_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> list[TaskGroup]:
        """查询任务组列表

        Args:
            user_id: 用户ID过滤条件（可选）
            model_id: 模型ID过滤条件（可选）

        Returns:
            任务组列表
        """
        stmt = select(TaskGroup)

        if user_id is not None:
            stmt = stmt.where(TaskGroup.user_id == user_id)

        if model_id is not None:
            stmt = stmt.where(TaskGroup.model_id == model_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, task_group_id: str) -> bool:
        """删除任务组

        Args:
            task_group_id: 任务组ID

        Returns:
            删除是否成功
        """
        task_group = await self.get_by_id(task_group_id)
        if task_group is None:
            return False

        await self.session.delete(task_group)
        await self.session.flush()
        return True
