"""PrivateConfigManager 用户私有检测配置管理模块

依赖模块: DataProcessor, UserCenter, LLMRegistry (via interfaces)
被依赖模块: StateScheduler
"""

import json
import os
from pathlib import Path
from typing import Literal, Optional

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_registry_interface import LLMRegistryInterface
from sdpj.drivers.user_center_interface import UserCenterInterface

from .private_config_manager_interface import PrivateConfigManagerInterface


class PrivateConfigManager(PrivateConfigManagerInterface):
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
        except ValueError:
            return False, None

    async def read_config(self, config_id: int) -> Optional[dict]:
        return await self._user_center.read_private_config(config_id)

    async def read_configs_batch(self, config_ids: list[int]) -> dict[int, dict]:
        """批量读取配置内容"""
        return await self._user_center.read_private_configs_batch(config_ids)

    async def update_config(self, config_id: int, config_content: dict) -> tuple[bool, str]:
        model_id = config_content.get("model_id") or config_content.get("model")
        try:
            success = await self._user_center.update_private_config(config_id, config_content)
            if not success:
                return False, "更新失败"
            # 热重载：如果适配器已注册，用新配置重新注册以更新内存中的实例
            if model_id:
                available, _ = await self._llm_registry.is_model_available(model_id)
                if available:
                    await self._llm_registry.unregister_private_model(model_id)
                adapter_content = json.dumps(config_content, ensure_ascii=False)
                ok, _, err = await self._llm_registry.register_private_model(adapter_content, model_id)
                if not ok:
                    return True, f"配置已更新但适配器热重载失败: {err}"
            return True, ""
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
                    configs.append(
                        {
                            "config_id": rid,
                            "content": configs_map[rid],
                        }
                    )
        for r in shared:
            if r.get("resource_type") == self.RESOURCE_TYPE_CONFIG and r["resource_id"] not in {
                c["config_id"] for c in configs
            }:
                rid = r["resource_id"]
                if rid in configs_map:
                    configs.append(
                        {
                            "config_id": rid,
                            "content": configs_map[rid],
                            "shared": True,
                        }
                    )
        return configs

    async def query_datasets(self) -> list[dict]:
        return await self._data_processor.get_all_datasets()

    async def upload_adapter(self, adapter_content: str, model_id: str, user_id: int) -> tuple[bool, str, int | None]:
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

    async def upload_dataset(self, name: str, risk_type: str, samples: list[dict], user_id: int) -> tuple[bool, dict]:
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
            name=name, sample_count=sample_count, file_path=file_path, resource_id=resource_id
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

    async def import_dataset_file(self, user_id: int, filename: str, content: bytes, username: str) -> dict:
        """导入用户数据集文件"""
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError as e:
            return {"success": False, "error": f"编码错误: {str(e)}"}

        try:
            if filename.endswith(".jsonl"):
                lines = text_content.strip().split("\n")
                sample_count = 0
                for line in lines:
                    if line.strip():
                        json.loads(line)
                        sample_count += 1
            elif filename.endswith(".json"):
                data = json.loads(text_content)
                sample_count = len(data) if isinstance(data, list) else 1
            elif filename.endswith(".csv"):
                lines = text_content.strip().split("\n")
                sample_count = max(0, len(lines) - 1)
            else:
                return {"success": False, "error": "不支持的文件格式，仅支持 .json, .jsonl, .csv"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"文件格式错误: {str(e)}"}

        base_path = Path("sdpj/infrastructure/database/sample_db/user_datasets") / username
        base_path.mkdir(parents=True, exist_ok=True)

        safe_filename = filename.replace(" ", "_")
        use_direct_name = False
        if safe_filename.startswith("user_datasets_"):
            safe_filename = safe_filename[len("user_datasets_") :]
            use_direct_name = True
        file_path = base_path / safe_filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        if use_direct_name:
            dataset_name = Path(safe_filename).stem
        else:
            dataset_name = f"user_datasets/{username}/{Path(safe_filename).stem}"
        dataset_id, resource_id = await self.add_custom_dataset(
            user_id=user_id, name=dataset_name, sample_count=sample_count, file_path=str(file_path)
        )

        return {"success": True, "dataset_id": dataset_id}

    # ── LLMRegistry 委托方法（供 StateScheduler 通过本模块间接调用，避免越层依赖）──

    async def initialize_registry(self) -> bool:
        return await self._llm_registry.initialize()

    async def shutdown_registry(self) -> bool:
        return await self._llm_registry.shutdown()

    async def is_model_available(self, model_id: str) -> tuple[bool, any]:
        return await self._llm_registry.is_model_available(model_id)

    def get_adapter_info(self, model_id: str) -> dict:
        return self._llm_registry.get_adapter_info(model_id)

    async def register_private_model(self, adapter_content: str, model_id: str) -> tuple[bool, str, str]:
        return await self._llm_registry.register_private_model(adapter_content, model_id)

    async def unregister_private_model(self, model_id: str) -> tuple[bool, str]:
        return await self._llm_registry.unregister_private_model(model_id)

    async def export_dataset_file(self, dataset_id: int, username: str | None = None) -> dict | None:
        """导出数据集文件"""
        datasets = await self.query_datasets()
        dataset = None
        for ds in datasets:
            if ds.get("dataset_id") == dataset_id:
                dataset = ds
                break
        if not dataset:
            return None

        dataset_name = dataset.get("name", "")
        resource_id = dataset.get("resource_id")
        base_path = Path(os.getcwd()) / "sdpj" / "infrastructure" / "database" / "sample_db"

        if resource_id is not None:
            if not username:
                username = str(resource_id)
            if dataset_name.startswith("user_datasets/"):
                file_path = base_path / dataset_name
            else:
                file_path = base_path / "user_datasets" / username / f"{dataset_name}.jsonl"
        else:
            file_path = base_path / f"{dataset_name}.jsonl"

        file_content = None
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
            except Exception:
                file_content = json.dumps(dataset, ensure_ascii=False, indent=2)
        else:
            file_content = json.dumps(dataset, ensure_ascii=False, indent=2)

        return {"content": file_content, "filename": Path(dataset_name).name + ".jsonl"}
