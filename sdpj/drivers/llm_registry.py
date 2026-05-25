"""LLMRegistry - 大模型注册中心实现

职责:
1. 启动时批量注册已入库大模型
2. 查询已注册大模型清单
3. 按标识校验大模型是否可用
4. 注册用户上传的私有大模型
5. 注销用户移除的私有大模型
6. 关闭期批量销毁全部服务实例

依赖: LLMAdapterLib, UtilsLib
"""

from typing import Optional

from sdpj.drivers.llm_registry_interface import ModelInfo
from sdpj.infrastructure.llm_adapters.errors import (
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    AdapterValidationError,
    LLMServiceInstance,
)
from sdpj.infrastructure.llm_adapters.llm_adapter_interface import (
    LLMAdapterLibInterface,
)
from sdpj.infrastructure.utils.utils_interface import UtilsInterface


class LLMRegistry:
    """大模型注册中心"""

    def __init__(
        self,
        adapter_lib: LLMAdapterLibInterface,
        utils_lib: UtilsInterface,
    ):
        self._adapter_lib = adapter_lib
        self._utils = utils_lib
        self._registry: dict[str, LLMServiceInstance] = {}

    async def initialize(self) -> bool:
        try:
            adapters = self._adapter_lib.list_adapters()
        except Exception:
            return False
        failed_models: list[str] = []
        for adapter_meta in adapters:
            model_id = adapter_meta.get("model_id")
            if not model_id:
                continue
            try:
                instance = await self._adapter_lib.get_service_instance(model_id)
                self._registry[model_id] = instance
            except (AdapterNotFoundError, Exception) as e:
                failed_models.append(f"{model_id}: {e}")
        if failed_models:
            import sys

            print(
                f"[LLMRegistry] 以下适配器初始化失败: {', '.join(failed_models)}", file=sys.stderr
            )
            return False
        return True

    async def list_registered_models(self) -> list[ModelInfo]:
        result: list[ModelInfo] = []
        for model_id in self._registry:
            try:
                meta = self._adapter_lib.get_adapter_info(model_id)
                result.append(
                    ModelInfo(
                        model_id=model_id,
                        adapter_name=meta.get("adapter_name", "openai_compatible"),
                        version=meta.get("version", "1.0"),
                        description=meta.get("description", ""),
                        supported_features=meta.get("supported_features", []),
                    )
                )
            except AdapterNotFoundError:
                result.append(ModelInfo(model_id=model_id, adapter_name="unknown", version="0.0"))
        return result

    async def is_model_available(self, model_id: str) -> tuple[bool, Optional[LLMServiceInstance]]:
        instance = self._registry.get(model_id)
        if instance is not None and instance.active:
            return True, instance
        return False, None

    async def register_private_model(
        self,
        adapter_content: str,
        model_id: str,
    ) -> tuple[bool, str, str]:
        try:
            is_valid, error_msg = self._utils.validate_file_format(adapter_content, "json")
            if not is_valid:
                return False, "", f"适配器配置格式校验失败: {error_msg}"

            instance = await self._adapter_lib.install_adapter(model_id, adapter_content)
            self._registry[model_id] = instance
            return True, model_id, ""

        except AdapterAlreadyExistsError:
            return False, "", f"模型 '{model_id}' 已存在"
        except AdapterValidationError as e:
            return False, "", f"适配器校验失败: {e}"
        except Exception as e:
            return False, "", f"注册失败: {e}"

    async def unregister_private_model(self, model_id: str) -> tuple[bool, str]:
        try:
            if model_id not in self._registry:
                return False, f"模型 '{model_id}' 未注册"

            self._registry.pop(model_id)
            await self._adapter_lib.remove_adapter(model_id)
            return True, ""

        except AdapterNotFoundError:
            return False, f"模型 '{model_id}' 适配器不存在"
        except Exception as e:
            return False, f"注销失败: {e}"

    def get_adapter_info(self, model_id: str) -> dict:
        """按大模型标识查询适配器元信息"""
        try:
            return self._adapter_lib.get_adapter_info(model_id)
        except AdapterNotFoundError:
            return {}

    async def shutdown(self) -> bool:
        for model_id, instance in list(self._registry.items()):
            try:
                await self._adapter_lib.destroy_service_instance(instance)
            except Exception:
                pass
        self._registry.clear()
        return True

    async def close_adapter_sessions(self) -> None:
        await self._adapter_lib.close_sessions()
