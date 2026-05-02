"""数据集仓储层实现

提供数据集的 CRUD 操作。
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..models import Dataset


class DatasetRepository:
    """数据集仓储

    封装数据集的数据访问逻辑。
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(self, name: str, risk_type: str) -> Dataset:
        """创建数据集

        Args:
            name: 数据集名称
            risk_type: 安全风险类型

        Returns:
            创建的数据集对象

        Raises:
            ValueError: 数据集名称重复时抛出
        """
        dataset = Dataset(name=name, risk_type=risk_type)
        self.session.add(dataset)

        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"数据集名称 '{name}' 已存在") from e

        return dataset

    async def delete(self, dataset_id: int) -> bool:
        """删除数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果（True 表示成功）
        """
        dataset = await self.get_by_id(dataset_id)
        if dataset is None:
            return False

        await self.session.delete(dataset)
        await self.session.flush()
        return True

    async def get_all(self) -> list[Dataset]:
        """查询所有数据集

        Returns:
            数据集列表
        """
        stmt = select(Dataset).order_by(Dataset.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """按 ID 查询数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            数据集对象，不存在时返回 None
        """
        stmt = select(Dataset).where(Dataset.dataset_id == dataset_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Dataset]:
        """按名称查询数据集

        Args:
            name: 数据集名称

        Returns:
            数据集对象，不存在时返回 None
        """
        stmt = select(Dataset).where(Dataset.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_risk_type(self, risk_type: str) -> list[Dataset]:
        """按安全风险类型筛选数据集

        Args:
            risk_type: 安全风险类型

        Returns:
            匹配的数据集列表
        """
        stmt = select(Dataset).where(Dataset.risk_type == risk_type).order_by(Dataset.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
