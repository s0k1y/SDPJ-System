"""PocPoolCache 仓储层.

提供 PoC 池缓存的数据访问操作.
"""

from typing import TYPE_CHECKING, cast

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.result_db.models import PocPoolCache

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult


class PocPoolCacheRepository:
    """PoC 池缓存仓储."""

    def __init__(self, session: AsyncSession) -> None:  # noqa: D107
        self.session = session

    async def get_by_model_id(self, model_id: str) -> list[PocPoolCache]:  # noqa: D102
        stmt = (
            select(PocPoolCache)
            .where(PocPoolCache.model_id == model_id)
            .order_by(PocPoolCache.score.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_batch(self, entries: list[PocPoolCache]) -> None:  # noqa: D102
        self.session.add_all(entries)
        await self.session.flush()

    async def delete_by_model_id(self, model_id: str) -> int:  # noqa: D102
        stmt = delete(PocPoolCache).where(PocPoolCache.model_id == model_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return cast("CursorResult", result).rowcount
