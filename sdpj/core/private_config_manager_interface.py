"""PrivateConfigManager 接口定义"""
from typing import Protocol


class PrivateConfigManagerInterface(Protocol):
    """用户私有检测配置管理接口"""

    async def init(self) -> None:
        """初始化配置管理器"""
        ...

    async def create_config(self, user_id: int, config_data: dict) -> int:
        """创建私有配置

        Args:
            user_id: 用户ID
            config_data: 配置数据

        Returns:
            配置ID
        """
        ...

    async def get_config(self, config_id: int) -> dict:
        """获取配置

        Args:
            config_id: 配置ID

        Returns:
            配置数据
        """
        ...

    async def update_config(self, config_id: int, config_data: dict) -> bool:
        """更新配置

        Args:
            config_id: 配置ID
            config_data: 配置数据

        Returns:
            更新成功返回True
        """
        ...

    async def delete_config(self, config_id: int) -> bool:
        """删除配置

        Args:
            config_id: 配置ID

        Returns:
            删除成功返回True
        """
        ...
