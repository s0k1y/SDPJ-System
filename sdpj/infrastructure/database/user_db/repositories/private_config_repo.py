"""私有检测配置仓储层.

负责私有检测配置内容表的 CRUD 操作.
"""

import json
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sdpj.infrastructure.database.user_db.models import PrivateConfig

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult


class PrivateConfigRepository:
    """私有检测配置仓储.

    职责:
    - 写入私有检测配置内容
    - 按 ID 读取私有检测配置内容
    - 更新私有检测配置内容
    - 删除私有检测配置内容
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化私有检测配置仓储.

        Args:
            session: 数据库会话

        """
        self._session = session

    async def create(self, config_id: int, config_content: dict) -> PrivateConfig:
        """写入私有检测配置内容.

        Args:
            config_id: 配置 ID(等同于其对应资源的资源 ID)
            config_content: 配置内容 JSON

        Returns:
            新创建的私有配置对象

        Raises:
            ValueError: 对应资源 ID 不存在时抛出
            ValueError: 同配置 ID 已有内容时抛出

        """
        # 检查是否已存在
        existing = await self.get_by_id(config_id)
        if existing:
            msg = f"配置 ID {config_id} 已存在,请使用更新操作"
            raise ValueError(msg)

        config_json = json.dumps(config_content, ensure_ascii=False)
        private_config = PrivateConfig(config_id=config_id, config_content=config_json)
        self._session.add(private_config)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            msg = f"资源 ID {config_id} 不存在"
            raise ValueError(msg) from e
        return private_config

    async def get_by_id(self, config_id: int) -> dict | None:
        """按 ID 读取私有检测配置内容.

        Args:
            config_id: 配置 ID

        Returns:
            配置内容 JSON,不存在时返回 None

        """
        stmt = select(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        private_config = result.scalar_one_or_none()

        if not private_config:
            return None

        return cast("dict[Any, Any]", json.loads(private_config.config_content))

    async def update(self, config_id: int, config_content: dict) -> bool:
        """更新私有检测配置内容.

        Args:
            config_id: 配置 ID
            config_content: 新配置内容 JSON

        Returns:
            更新结果(True 表示成功)

        Raises:
            ValueError: 配置 ID 不存在时抛出

        """
        stmt = select(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        private_config = result.scalar_one_or_none()

        if not private_config:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        config_json = json.dumps(config_content, ensure_ascii=False)
        private_config.config_content = config_json
        await self._session.flush()
        return True

    async def delete(self, config_id: int) -> bool:
        """删除私有检测配置内容.

        Args:
            config_id: 配置 ID

        Returns:
            删除结果(True 表示成功)

        """
        stmt = delete(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return cast("CursorResult", result).rowcount > 0

    async def get_by_ids(self, config_ids: list[int]) -> dict[int, dict]:
        """批量按 ID 读取私有检测配置内容.

        Args:
            config_ids: 配置 ID 列表

        Returns:
            {config_id: config_content_dict} 映射,不存在的 ID 不出现在结果中

        """
        if not config_ids:
            return {}
        stmt = select(PrivateConfig).where(PrivateConfig.config_id.in_(config_ids))
        result = await self._session.execute(stmt)
        configs = result.scalars().all()
        return {c.config_id: json.loads(c.config_content) for c in configs}
