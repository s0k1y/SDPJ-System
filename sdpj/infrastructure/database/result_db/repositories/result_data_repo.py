"""ResultData 仓储层

提供检测结果数据的数据访问操作。
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ResultData


class ResultDataRepository:
    """检测结果数据仓储"""

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(
        self,
        result_data_id: str,
        report_id: str,
        risk_subclass: str,
        model_output: str,
        compliance_result: str
    ) -> ResultData:
        """创建结果数据条目

        Args:
            result_data_id: 结果数据ID
            report_id: 报告ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果

        Returns:
            创建的结果数据对象
        """
        result_data = ResultData(
            result_data_id=result_data_id,
            report_id=report_id,
            risk_subclass=risk_subclass,
            model_output=model_output,
            compliance_result=compliance_result
        )
        self.session.add(result_data)
        await self.session.flush()
        return result_data

    async def get_by_id(self, result_data_id: str) -> Optional[ResultData]:
        """按ID查询结果数据

        Args:
            result_data_id: 结果数据ID

        Returns:
            结果数据对象，不存在时返回None
        """
        stmt = select(ResultData).where(ResultData.result_data_id == result_data_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_report(self, report_id: str) -> list[ResultData]:
        """按报告ID查询结果数据列表

        Args:
            report_id: 报告ID

        Returns:
            结果数据列表
        """
        stmt = select(ResultData).where(ResultData.report_id == report_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, result_data_id: str) -> bool:
        """删除结果数据

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
