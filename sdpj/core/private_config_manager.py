"""PrivateConfigManager 用户私有检测配置管理模块

依赖模块: DataProcessor, UserCenter, LLMRegistry (via interfaces)
被依赖模块: StateScheduler
"""
from typing import Optional, Literal

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_registry_interface import LLMRegistryInterface
from sdpj.drivers.user_center_interface import UserCenterInterface


class PrivateConfigManager:
    """用户私有检测配置管理"""

    RESOURCE_TYPE_CONFIG = "private_config"
    RESOURCE_TYPE_ADAPTER = "private_adapter"
    RESOURCE_TYPE_DATASET = "private_dataset"

    def __init__(
        self,
        data_processor: DataProcessorInterface,
        user_center: UserCenterInterface,
        llm_registry: LLMRegistryInterface,
    ):
        self._data_processor = data_processor
        self._user_center = user_center
        self._llm_registry = llm_registry

    async def create_config(self, user_id: int, config_content: dict) -> tuple[bool, int | None]:
        # 私有配置用于注册新模型，不需要预先检查模型是否存在
        # model_id 会在配置保存后通过 LLMRegistry 注册
        try:
            resource_id = await self._user_center.register_resource(self.RESOURCE_TYPE_CONFIG, user_id)
            await self._user_center.write_private_config(resource_id, config_content)
            return True, resource_id
        except ValueError as e:
            return False, None

    async def read_config(self, config_id: int) -> Optional[dict]:
        return await self._user_center.read_private_config(config_id)

    async def read_configs_batch(self, config_ids: list[int]) -> dict[int, dict]:
        """批量读取配置内容"""
        return await self._user_center.read_private_configs_batch(config_ids)

    async def update_config(self, config_id: int, config_content: dict) -> tuple[bool, str]:
        model_id = config_content.get("model_id")
        if model_id:
            available, _ = await self._llm_registry.is_model_available(model_id)
            if not available:
                return False, f"大模型 '{model_id}' 不可用"
        try:
            success = await self._user_center.update_private_config(config_id, config_content)
            return (True, "") if success else (False, "更新失败")
        except ValueError as e:
            return False, str(e)

    async def delete_config(self, config_id: int) -> bool:
        return await self._user_center.delete_resource(config_id)

    async def list_configs(self, user_id: int) -> list[dict]:
        owned = await self._user_center.get_resources_by_owner(user_id)
        shared = await self._user_center.get_resources_shared_with(user_id)

        config_ids = []
        seen_ids = set()
        for r in owned:
            if r.get("resource_type") == self.RESOURCE_TYPE_CONFIG:
                rid = r["resource_id"]
                config_ids.append(rid)
                seen_ids.add(rid)
        for r in shared:
            if r.get("resource_type") == self.RESOURCE_TYPE_CONFIG and r["resource_id"] not in seen_ids:
                rid = r["resource_id"]
                config_ids.append(rid)
                seen_ids.add(rid)

        if not config_ids:
            return []

        configs_map = await self._user_center.read_private_configs_batch(config_ids)

        configs = []
        for r in owned:
            if r.get("resource_type") == self.RESOURCE_TYPE_CONFIG:
                rid = r["resource_id"]
                if rid in configs_map:
                    configs.append({
                        "config_id": rid,
                        "content": configs_map[rid],
                    })
        for r in shared:
            if r.get("resource_type") == self.RESOURCE_TYPE_CONFIG and r["resource_id"] not in {c["config_id"] for c in configs}:
                rid = r["resource_id"]
                if rid in configs_map:
                    configs.append({
                        "config_id": rid,
                        "content": configs_map[rid],
                        "shared": True,
                    })
        return configs

    async def query_datasets(self) -> list[dict]:
        return await self._data_processor.get_all_datasets()

    async def upload_adapter(
        self, adapter_content: str, model_id: str, user_id: int
    ) -> tuple[bool, str, int | None]:
        valid, msg = self._data_processor.validate_file_format(adapter_content, "json")
        if not valid:
            return False, f"文件格式校验失败: {msg}", None

        success, registered_id, error = await self._llm_registry.register_private_model(adapter_content, model_id)
        if not success:
            return False, error, None

        resource_id = await self._user_center.register_resource(self.RESOURCE_TYPE_ADAPTER, user_id)
        return True, registered_id, resource_id

    async def remove_adapter(self, model_id: str, resource_id: int) -> tuple[bool, str]:
        success, error = await self._llm_registry.unregister_private_model(model_id)
        if not success:
            return False, error
        await self._user_center.delete_resource(resource_id)
        return True, ""

    async def upload_dataset(
        self, name: str, risk_type: str, samples: list[dict], user_id: int
    ) -> tuple[bool, dict]:
        if not name or not risk_type:
            return False, {"error": "name 和 risk_type 不能为空"}
        for i, s in enumerate(samples):
            if not isinstance(s, dict) or "poc" not in s or "subtype" not in s:
                return False, {"error": f"样本[{i}]缺少必要字段 poc/subtype"}
        try:
            resource_id = await self._user_center.register_resource(self.RESOURCE_TYPE_DATASET, user_id)
            result = await self._data_processor.import_private_dataset(name, risk_type, samples, resource_id)
            result["resource_id"] = resource_id
            return True, result
        except Exception as e:
            return False, {"error": str(e)}

    async def remove_dataset(self, dataset_id: int, resource_id: int | None = None) -> bool:
        success = await self._data_processor.remove_dataset(dataset_id)
        if success and resource_id is not None:
            await self._user_center.delete_resource(resource_id)
        return success

    async def add_custom_dataset(self, user_id: int, name: str, sample_count: int, file_path: str) -> tuple[int, int]:
        """添加自定义数据集到数据库

        Returns:
            (dataset_id, resource_id) 元组
        """
        resource_id = await self._user_center.register_resource(self.RESOURCE_TYPE_DATASET, user_id)

        dataset_id = await self._data_processor.add_dataset_record(
            name=name,
            sample_count=sample_count,
            file_path=file_path,
            resource_id=resource_id
        )

        return dataset_id, resource_id

    async def export_config(self, config_id: int, target_format: Literal["json", "yaml"]) -> str:
        content = await self._user_center.read_private_config(config_id)
        if content is None:
            raise ValueError(f"配置 {config_id} 不存在")
        return self._data_processor.serialize_data(content, target_format)

    async def import_config(self, file_content: str, user_id: int) -> tuple[bool, int | None]:
        valid, msg = self._data_processor.validate_file_format(file_content, "json")
        if not valid:
            valid, msg = self._data_processor.validate_file_format(file_content, "yaml")
        if not valid:
            return False, None

        try:
            config_content = self._data_processor.deserialize_data(file_content, "json")
        except Exception:
            try:
                config_content = self._data_processor.deserialize_data(file_content, "yaml")
            except Exception:
                return False, None

        model_id = config_content.get("model_id")
        if model_id:
            available, _ = await self._llm_registry.is_model_available(model_id)
            if not available:
                return False, None

        return await self.create_config(user_id, config_content)
