"""LLMAdapterLib — 大模型 API 适配库（实现 LLMAdapterLibInterface）"""

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    ErrorCategory,
    LLMServiceInstance,
    StandardizedLLMError,
)
from sdpj.infrastructure.llm_adapters.loader import load_adapter_from_config


class LLMAdapterLib:
    """大模型 API 适配库

    管理适配器制品的入库/移除/查询，以及服务实例的创建/销毁。
    无内置适配器，所有 LLM 均通过用户 JSON 配置接入。
    """

    def __init__(self) -> None:
        self._adapters: dict[str, LLMAdapter] = {}
        self._instances: dict[str, LLMServiceInstance] = {}
        self._metadata: dict[str, dict] = {}

    # ===== 职责 1: 入库适配器 =====
    async def install_adapter(self, model_id: str, adapter_content: str) -> LLMServiceInstance:
        if model_id in self._adapters:
            raise AdapterAlreadyExistsError(f"Adapter '{model_id}' already exists")

        import json

        config = json.loads(adapter_content)
        adapter = load_adapter_from_config(model_id, config)
        self._adapters[model_id] = adapter
        self._metadata[model_id] = {
            "model_id": model_id,
            **adapter.get_metadata(),
        }
        instance = LLMServiceInstance(model_id=model_id, adapter=adapter)
        self._instances[model_id] = instance
        return instance

    # ===== 职责 2: 移除适配器 =====
    async def remove_adapter(self, model_id: str) -> bool:
        if model_id not in self._adapters:
            raise AdapterNotFoundError(f"Adapter '{model_id}' not found")
        if model_id in self._instances:
            await self._instances[model_id].destroy()
            del self._instances[model_id]
        del self._adapters[model_id]
        del self._metadata[model_id]
        return True

    # ===== 职责 3: 列出适配器 =====
    def list_adapters(self) -> list[dict]:
        return list(self._metadata.values())

    # ===== 职责 4: 查询适配器 =====
    def get_adapter_info(self, model_id: str) -> dict:
        if model_id not in self._metadata:
            raise AdapterNotFoundError(f"Adapter '{model_id}' not found")
        return self._metadata[model_id]

    # ===== 职责 5: 获取服务实例 =====
    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:
        if model_id in self._instances and self._instances[model_id].active:
            return self._instances[model_id]
        if model_id not in self._adapters:
            raise AdapterNotFoundError(f"Adapter '{model_id}' not found, cannot create instance")
        instance = LLMServiceInstance(model_id=model_id, adapter=self._adapters[model_id])
        self._instances[model_id] = instance
        return instance

    # ===== 职责 6: 销毁服务实例 =====
    async def destroy_service_instance(self, instance: LLMServiceInstance) -> bool:
        await instance.destroy()
        self._instances.pop(instance.model_id, None)
        return True

    # ===== 职责 7: 错误标准化 =====
    @staticmethod
    def standardize_error(exc: Exception) -> StandardizedLLMError:
        if isinstance(exc, StandardizedLLMError):
            return exc
        import aiohttp

        if isinstance(exc, aiohttp.ServerTimeoutError):
            return StandardizedLLMError(ErrorCategory.TIMEOUT, str(exc), original_error=exc)
        if isinstance(exc, aiohttp.ClientResponseError):
            s = exc.status
            if s == 401:
                cat = ErrorCategory.AUTH
            elif s == 429:
                cat = ErrorCategory.RATE_LIMIT
            elif 400 <= s < 500:
                cat = ErrorCategory.INVALID_REQUEST
            else:
                cat = ErrorCategory.SERVER_ERROR
            return StandardizedLLMError(cat, str(exc), status_code=s, original_error=exc)
        if isinstance(exc, aiohttp.ClientError):
            return StandardizedLLMError(ErrorCategory.NETWORK, str(exc), original_error=exc)
        return StandardizedLLMError(ErrorCategory.UNKNOWN, str(exc), original_error=exc)
