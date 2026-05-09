"""PocPoolCache 仓储层

提供 PoC 池缓存的数据访问操作。
"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PocPoolCache


class PocPoolCacheRepository:
    """PoC 池缓存仓储"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_model_id(self, model_id: str) -> list[PocPoolCache]:
        stmt = select(PocPoolCache).where(PocPoolCache.model_id == model_id).order_by(PocPoolCache.score.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_batch(self, entries: list[PocPoolCache]) -> None:
        self.session.add_all(entries)
        await self.session.flush()

    async def delete_by_model_id(self, model_id: str) -> int:
        stmt = delete(PocPoolCache).where(PocPoolCache.model_id == model_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
