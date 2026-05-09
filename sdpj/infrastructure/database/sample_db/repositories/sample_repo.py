"""检测样本仓储层实现

提供检测样本的 CRUD 操作。
"""

from typing import Optional

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DetectionSample


class SampleRepository:
    """检测样本仓储

    封装检测样本的数据访问逻辑。
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(self, subtype: str, poc: str, dataset_id: int) -> DetectionSample:
        """创建检测样本

        Args:
            subtype: 风险具体子类 ST
            poc: 漏洞概念验证数据 PoC
            dataset_id: 所属数据集 ID

        Returns:
            创建的样本对象

        Raises:
            ValueError: 所属数据集 ID 不存在时抛出
        """
        sample = DetectionSample(subtype=subtype, poc=poc, dataset_id=dataset_id)
        self.session.add(sample)

        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"所属数据集 ID {dataset_id} 不存在") from e

        return sample

    async def delete(self, sample_id: int) -> bool:
        """删除检测样本

        Args:
            sample_id: 样本 ID

        Returns:
            删除结果（True 表示成功）
        """
        sample = await self.get_by_id(sample_id)
        if sample is None:
            return False

        await self.session.delete(sample)
        await self.session.flush()
        return True

    async def get_by_id(self, sample_id: int) -> Optional[DetectionSample]:
        """按 ID 查询样本

        Args:
            sample_id: 样本 ID

        Returns:
            样本对象，不存在时返回 None
        """
        stmt = select(DetectionSample).where(DetectionSample.sample_id == sample_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_dataset(self, dataset_id: int) -> list[DetectionSample]:
        """按数据集 ID 查询所有样本

        Args:
            dataset_id: 数据集 ID

        Returns:
            该数据集下的所有样本列表
        """
        stmt = (
            select(DetectionSample)
            .where(DetectionSample.dataset_id == dataset_id)
            .order_by(DetectionSample.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_risk_type(self, risk_type: str) -> list[DetectionSample]:
        """按风险类型查询所有样本（JOIN 数据集表）

        Args:
            risk_type: 安全风险类型

        Returns:
            匹配的所有样本列表
        """
        from ..models import Dataset

        stmt = (
            select(DetectionSample)
            .join(Dataset, DetectionSample.dataset_id == Dataset.dataset_id)
            .where(Dataset.risk_type == risk_type)
            .order_by(DetectionSample.dataset_id, DetectionSample.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_dataset(self, dataset_id: int) -> int:
        """删除指定数据集下的所有样本

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除的行数
        """
        stmt = sa_delete(DetectionSample).where(DetectionSample.dataset_id == dataset_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
