from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TargetModel


class TargetModelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_id: str) -> Optional[TargetModel]:
        result = await self.session.execute(
            select(TargetModel).where(TargetModel.model_id == model_id)
        )
        return result.scalar_one_or_none()

    async def register(self, model_id: str) -> TargetModel:
        existing = await self.get_by_id(model_id)
        if existing:
            return existing
        obj = TargetModel(model_id=model_id)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_all(self) -> list[TargetModel]:
        result = await self.session.execute(select(TargetModel))
        return list(result.scalars().all())
