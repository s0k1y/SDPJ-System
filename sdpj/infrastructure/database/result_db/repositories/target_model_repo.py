"""Module docstring."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.result_db.models import TargetModel


class TargetModelRepository:  # noqa: D101
    def __init__(self, session: AsyncSession) -> None:  # noqa: D107
        self.session = session

    async def get_by_id(self, model_id: str) -> TargetModel | None:  # noqa: D102
        result = await self.session.execute(
            select(TargetModel).where(TargetModel.model_id == model_id),
        )
        return result.scalar_one_or_none()

    async def register(self, model_id: str) -> TargetModel:  # noqa: D102
        existing = await self.get_by_id(model_id)
        if existing:
            return existing
        obj = TargetModel(model_id=model_id)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_all(self) -> list[TargetModel]:  # noqa: D102
        result = await self.session.execute(select(TargetModel))
        return list(result.scalars().all())
