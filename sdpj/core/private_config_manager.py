"""PrivateConfigManager 用户私有检测配置管理模块"""
from sdpj.drivers.data_processor import DataProcessor
from sdpj.drivers.llm_registry import LLMRegistry
from sdpj.drivers.user_center import UserCenter


class PrivateConfigManager:
    """用户私有检测配置管理"""

    def __init__(self):
        self.data_processor = DataProcessor()
        self.llm_registry = LLMRegistry()
        self.user_center = UserCenter()
        self._initialized = False

    async def init(self):
        if not self._initialized:
            await self.data_processor.init()
            await self.llm_registry.startup()
            await self.user_center.init()
            self._initialized = True

    async def create_config(self, user_id: int, config_data: dict) -> tuple[bool, int | None]:
        model_id = config_data.get("model_id")
        available, _ = self.llm_registry.check_model_available(model_id)
        if not available:
            return False, None
        resource_id = await self.user_center.register_resource("config", user_id)
        return True, resource_id

    async def query_datasets(self) -> list[dict]:
        return await self.data_processor.query_datasets()
