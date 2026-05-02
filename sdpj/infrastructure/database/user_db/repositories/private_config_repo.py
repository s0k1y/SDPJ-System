"""私有检测配置仓储层

负责私有检测配置内容表的 CRUD 操作。
"""

import json
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models import PrivateConfig


class PrivateConfigRepository:
    """私有检测配置仓储

    职责：
    - 写入私有检测配置内容
    - 按 ID 读取私有检测配置内容
    - 更新私有检测配置内容
    - 删除私有检测配置内容
    """

    def __init__(self, session: AsyncSession):
        """初始化私有检测配置仓储

        Args:
            session: 数据库会话
        """
        self._session = session

    async def create(self, config_id: int, config_content: dict) -> PrivateConfig:
        """写入私有检测配置内容

        Args:
            config_id: 配置 ID（等同于其对应资源的资源 ID）
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
            raise ValueError(f"配置 ID {config_id} 已存在，请使用更新操作")

        config_json = json.dumps(config_content, ensure_ascii=False)
        private_config = PrivateConfig(config_id=config_id, config_content=config_json)
        self._session.add(private_config)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ValueError(f"资源 ID {config_id} 不存在") from e
        return private_config

    async def get_by_id(self, config_id: int) -> Optional[dict]:
        """按 ID 读取私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            配置内容 JSON，不存在时返回 None
        """
        stmt = select(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        private_config = result.scalar_one_or_none()

        if not private_config:
            return None

        return json.loads(private_config.config_content)

    async def update(self, config_id: int, config_content: dict) -> bool:
        """更新私有检测配置内容

        Args:
            config_id: 配置 ID
            config_content: 新配置内容 JSON

        Returns:
            更新结果（True 表示成功）

        Raises:
            ValueError: 配置 ID 不存在时抛出
        """
        stmt = select(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        private_config = result.scalar_one_or_none()

        if not private_config:
            raise ValueError(f"配置 ID {config_id} 不存在")

        config_json = json.dumps(config_content, ensure_ascii=False)
        private_config.config_content = config_json
        await self._session.flush()
        return True

    async def delete(self, config_id: int) -> bool:
        """删除私有检测配置内容

        Args:
            config_id: 配置 ID

        Returns:
            删除结果（True 表示成功）
        """
        stmt = delete(PrivateConfig).where(PrivateConfig.config_id == config_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
