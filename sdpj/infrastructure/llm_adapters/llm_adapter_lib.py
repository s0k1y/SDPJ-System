"""LLMAdapterLib — 大模型 API 适配库(实现 LLMAdapterLibInterface)."""

import contextlib
from typing import TYPE_CHECKING

from sdpj.infrastructure.llm_adapters.errors import (
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    ErrorCategory,
    LLMServiceInstance,
    StandardizedLLMError,
)
from sdpj.infrastructure.llm_adapters.loader import load_adapter_from_config

if TYPE_CHECKING:
    from sdpj.infrastructure.llm_adapters.base import LLMAdapter


class LLMAdapterLib:
    """大模型 API 适配库.

    管理适配器制品的入库/移除/查询,以及服务实例的创建/销毁.
    无内置适配器,所有 LLM 均通过用户 JSON 配置接入.
    """

    def __init__(self) -> None:  # noqa: D107
        self._adapters: dict[str, LLMAdapter] = {}
        self._instances: dict[str, LLMServiceInstance] = {}
        self._metadata: dict[str, dict] = {}

    # ===== 职责 1: 入库适配器 =====
    async def install_adapter(self, model_id: str, adapter_content: str) -> LLMServiceInstance:  # noqa: D102
        if model_id in self._adapters:
            msg = f"Adapter '{model_id}' already exists"
            raise AdapterAlreadyExistsError(msg)

        import json  # noqa: PLC0415

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
    async def remove_adapter(self, model_id: str) -> bool:  # noqa: D102
        if model_id not in self._adapters:
            msg = f"Adapter '{model_id}' not found"
            raise AdapterNotFoundError(msg)
        if model_id in self._instances:
            await self._instances[model_id].destroy()
            del self._instances[model_id]
        del self._adapters[model_id]
        del self._metadata[model_id]
        return True

    # ===== 职责 3: 列出适配器 =====
    def list_adapters(self) -> list[dict]:  # noqa: D102
        return list(self._metadata.values())

    # ===== 职责 4: 查询适配器 =====
    def get_adapter_info(self, model_id: str) -> dict:  # noqa: D102
        if model_id not in self._metadata:
            msg = f"Adapter '{model_id}' not found"
            raise AdapterNotFoundError(msg)
        return self._metadata[model_id]

    # ===== 职责 5: 获取服务实例 =====
    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:  # noqa: D102
        if model_id in self._instances and self._instances[model_id].active:
            return self._instances[model_id]
        if model_id not in self._adapters:
            msg = f"Adapter '{model_id}' not found, cannot create instance"
            raise AdapterNotFoundError(msg)
        instance = LLMServiceInstance(model_id=model_id, adapter=self._adapters[model_id])
        self._instances[model_id] = instance
        return instance

    # ===== 职责 6: 销毁服务实例 =====
    async def destroy_service_instance(self, instance: LLMServiceInstance) -> bool:  # noqa: D102
        await instance.destroy()
        self._instances.pop(instance.model_id, None)
        return True

    # ===== 职责 7: 关闭所有服务实例的HTTP会话 =====
    async def close_sessions(self) -> None:  # noqa: D102
        for instance in list(self._instances.values()):
            with contextlib.suppress(Exception):
                await instance.destroy()

    # ===== 职责 7: 错误标准化 =====
    @staticmethod
    def standardize_error(exc: Exception) -> StandardizedLLMError:  # noqa: D102
        if isinstance(exc, StandardizedLLMError):
            return exc
        import asyncio  # noqa: PLC0415

        import aiohttp  # noqa: PLC0415

        if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
            return StandardizedLLMError(ErrorCategory.TIMEOUT, str(exc), original_error=exc)
        if isinstance(exc, aiohttp.ServerTimeoutError):
            return StandardizedLLMError(ErrorCategory.TIMEOUT, str(exc), original_error=exc)
        if isinstance(exc, aiohttp.ClientResponseError):
            s = exc.status
            if s == 401:  # noqa: PLR2004
                cat = ErrorCategory.AUTH
            elif s == 429:  # noqa: PLR2004
                cat = ErrorCategory.RATE_LIMIT
            elif 400 <= s < 500:  # noqa: PLR2004
                cat = ErrorCategory.INVALID_REQUEST
            else:
                cat = ErrorCategory.SERVER_ERROR
            return StandardizedLLMError(cat, str(exc), status_code=s, original_error=exc)
        if isinstance(exc, aiohttp.ClientError):
            return StandardizedLLMError(ErrorCategory.NETWORK, str(exc), original_error=exc)
        return StandardizedLLMError(ErrorCategory.UNKNOWN, str(exc), original_error=exc)
