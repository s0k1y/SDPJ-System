"""DetectionReport 仓储层

提供检测报告的数据访问操作。
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import DetectionReport, DetectionTask


class ReportRepository:
    """检测报告仓储"""

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(self, report_id: str, task_id: str) -> DetectionReport:
        """创建检测报告

        Args:
            report_id: 报告ID
            task_id: 任务ID

        Returns:
            创建的报告对象
        """
        report = DetectionReport(
            report_id=report_id,
            task_id=task_id
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_by_id(self, report_id: str) -> Optional[DetectionReport]:
        """按ID查询报告

        Args:
            report_id: 报告ID

        Returns:
            报告对象，不存在时返回None
        """
        stmt = select(DetectionReport).where(DetectionReport.report_id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_task_id(self, task_id: str) -> Optional[DetectionReport]:
        """按任务ID查询报告

        Args:
            task_id: 任务ID

        Returns:
            报告对象，不存在时返回None
        """
        stmt = select(DetectionReport).where(DetectionReport.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, task_group_id: Optional[str] = None) -> list[DetectionReport]:
        """查询报告列表

        Args:
            task_group_id: 任务组ID过滤条件（可选）

        Returns:
            报告列表
        """
        stmt = select(DetectionReport).options(selectinload(DetectionReport.detection_task))

        if task_group_id is not None:
            stmt = stmt.join(DetectionTask).where(DetectionTask.task_group_id == task_group_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, report_id: str) -> bool:
        """删除报告

        Args:
            report_id: 报告ID

        Returns:
            删除是否成功
        """
        report = await self.get_by_id(report_id)
        if report is None:
            return False

        await self.session.delete(report)
        await self.session.flush()
        return True
