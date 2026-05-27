"""DetectionTask 仓储层.

提供检测任务的数据访问操作.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.result_db.models import DetectionTask


class TaskRepository:
    """检测任务仓储."""

    def __init__(self, session: AsyncSession) -> None:  # noqa: D107
        self.session = session

    async def create(  # noqa: D102, PLR0913
        self,
        task_id: str,
        task_group_id: str,
        dataset_id: int,
        task_status: str,
        start_time: datetime,
        algorithm_type: str = "static",
        metadata_json: dict | None = None,
    ) -> DetectionTask:
        task = DetectionTask(
            task_id=task_id,
            task_group_id=task_group_id,
            dataset_id=dataset_id,
            task_status=task_status,
            algorithm_type=algorithm_type,
            metadata_json=metadata_json,
            start_time=start_time,
            end_time=None,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: str) -> DetectionTask | None:
        """按ID查询任务.

        Args:
            task_id: 任务ID

        Returns:
            任务对象,不存在时返回None

        """
        stmt = select(DetectionTask).where(DetectionTask.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_group_and_dataset(  # noqa: D102
        self, task_group_id: str, dataset_id: int,
        encoding_type: str | None = None,
    ) -> DetectionTask | None:
        stmt = select(DetectionTask).where(
            DetectionTask.task_group_id == task_group_id,
            DetectionTask.dataset_id == dataset_id,
        )
        result = await self.session.execute(stmt)
        tasks = result.scalars().all()

        if not tasks:
            return None

        if encoding_type is not None:
            for task in tasks:
                meta = task.metadata_json or {}
                if meta.get("encoding_type") == encoding_type:
                    return task
            return None

        if len(tasks) > 1:
            return tasks[0]

        return tasks[0]

    async def list_by_group(self, task_group_id: str) -> list[DetectionTask]:
        """按任务组ID查询任务列表.

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
        end_time: datetime | None = None,
        error_message: str | None = None,
    ) -> bool:
        """更新任务状态.

        Args:
            task_id: 任务ID
            task_status: 任务状态
            end_time: 结束时间(可选)
            error_message: 错误信息(可选)

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

    async def delete(self, task_id: str) -> bool:  # noqa: D102
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True

    async def list_non_terminal(self) -> list[DetectionTask]:  # noqa: D102
        stmt = select(DetectionTask).where(DetectionTask.task_status.in_(["pending", "running"]))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
