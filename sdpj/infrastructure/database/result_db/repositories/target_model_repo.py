"""TargetModel 仓储层

提供被测大模型的数据访问操作。
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import TargetModel


class TargetModelRepository:
    """被测大模型仓储"""

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create(self, model_id: str) -> TargetModel:
        """创建被测大模型记录

        Args:
            model_id: 模型ID

        Returns:
            创建的模型对象
        """
        target_model = TargetModel(model_id=model_id)
        self.session.add(target_model)
        await self.session.flush()
        return target_model

    async def get_by_id(self, model_id: str) -> Optional[TargetModel]:
        """按ID查询被测大模型

        Args:
            model_id: 模型ID

        Returns:
            模型对象，不存在时返回None
        """
        stmt = select(TargetModel).where(TargetModel.model_id == model_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, model_id: str) -> bool:
        """检查模型是否存在

        Args:
            model_id: 模型ID

        Returns:
            模型是否存在
        """
        model = await self.get_by_id(model_id)
        return model is not None
