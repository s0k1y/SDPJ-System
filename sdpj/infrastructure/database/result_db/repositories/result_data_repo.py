"""ResultData 仓储层.

提供检测结果数据的数据访问操作.
"""


from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.result_db.models import DetectionReport, DetectionTask, ResultData


class ResultDataRepository:
    """检测结果数据仓储."""

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储.

        Args:
            session: 异步数据库会话

        """
        self.session = session

    async def create(  # noqa: D417, PLR0913
        self,
        result_data_id: str,
        report_id: str,
        risk_subclass: str,
        poc: str,
        model_output: str,
        compliance_result: str,
        iteration_count: int | None = None,
    ) -> ResultData:
        """创建结果数据条目.

        Args:
            result_data_id: 结果数据ID
            report_id: 报告ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果
            iteration_count: 动态检测迭代次数(可选)

        Returns:
            创建的结果数据对象

        """
        result_data = ResultData(
            result_data_id=result_data_id,
            report_id=report_id,
            risk_subclass=risk_subclass,
            poc=poc,
            model_output=model_output,
            compliance_result=compliance_result,
            iteration_count=iteration_count,
        )
        self.session.add(result_data)
        await self.session.flush()
        return result_data

    async def create_batch(self, items: list[ResultData]) -> list[ResultData]:  # noqa: D102
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def get_by_id(self, result_data_id: str) -> ResultData | None:
        """按ID查询结果数据.

        Args:
            result_data_id: 结果数据ID

        Returns:
            结果数据对象,不存在时返回None

        """
        stmt = select(ResultData).where(ResultData.result_data_id == result_data_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_report(self, report_id: str) -> list[ResultData]:
        """按报告ID查询结果数据列表.

        Args:
            report_id: 报告ID

        Returns:
            结果数据列表

        """
        stmt = select(ResultData).where(ResultData.report_id == report_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_reports(self, report_ids: list[str]) -> list[ResultData]:
        """按多个报告ID批量查询结果数据.

        Args:
            report_ids: 报告ID列表

        Returns:
            匹配的结果数据列表

        """
        if not report_ids:
            return []
        stmt = select(ResultData).where(ResultData.report_id.in_(report_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_compliance(self) -> dict[str, int]:  # noqa: D102
        stmt = (
            select(
                ResultData.compliance_result,
                func.count(),
            )
            .join(DetectionReport, ResultData.report_id == DetectionReport.report_id)
            .join(DetectionTask, DetectionReport.task_id == DetectionTask.task_id)
            .where(DetectionTask.task_status.notin_(["cancelled", "no_jailbreak_risk"]))
            .group_by(ResultData.compliance_result)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def delete_by_report(self, report_id: str) -> int:
        stmt = select(ResultData).where(ResultData.report_id == report_id)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        for row in rows:
            await self.session.delete(row)
        if rows:
            await self.session.flush()
        return len(rows)

    async def delete(self, result_data_id: str) -> bool:
        """删除结果数据.

        Args:
            result_data_id: 结果数据ID

        Returns:
            删除是否成功

        """
        result_data = await self.get_by_id(result_data_id)
        if result_data is None:
            return False

        await self.session.delete(result_data)
        await self.session.flush()
        return True
