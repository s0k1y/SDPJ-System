"""DetectionTask 仓储层

提供检测任务的数据访问操作。
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import DetectionTask


class TaskRepository:
    """检测任务仓储"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        task_id: str,
        task_group_id: str,
        dataset_id: int,
        task_status: str,
        start_time: datetime,
        algorithm_type: str = "static",
        metadata_json: Optional[dict] = None,
    ) -> DetectionTask:
        task = DetectionTask(
            task_id=task_id,
            task_group_id=task_group_id,
            dataset_id=dataset_id,
            task_status=task_status,
            algorithm_type=algorithm_type,
            metadata_json=metadata_json,
            start_time=start_time,
            end_time=None
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: str) -> Optional[DetectionTask]:
        """按ID查询任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在时返回None
        """
        stmt = select(DetectionTask).where(DetectionTask.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_group(self, task_group_id: str) -> list[DetectionTask]:
        """按任务组ID查询任务列表

        Args:
            task_group_id: 任务组ID

        Returns:
            任务列表
        """
        stmt = select(DetectionTask).where(DetectionTask.task_group_id == task_group_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        task_id: str,
        task_status: str,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态

        Args:
            task_id: 任务ID
            task_status: 任务状态
            end_time: 结束时间（可选）
            error_message: 错误信息（可选）

        Returns:
            更新是否成功
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        task.task_status = task_status
        if end_time is not None:
            task.end_time = end_time
        if error_message is not None:
            task.error_message = error_message

        await self.session.flush()
        return True

    async def delete(self, task_id: str) -> bool:
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True

    async def list_non_terminal(self) -> list[DetectionTask]:
        stmt = select(DetectionTask).where(
            DetectionTask.task_status.in_(["pending", "running"])
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
