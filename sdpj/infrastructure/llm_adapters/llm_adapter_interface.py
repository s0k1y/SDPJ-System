"""LLMAdapterLib 接口定义(对应规格职责 1-8)."""

from typing import Protocol

from sdpj.infrastructure.llm_adapters.errors import (
    LLMServiceInstance,
    StandardizedLLMError,
)


class LLMAdapterLibInterface(Protocol):
    """大模型 API 适配库接口.

    覆盖规格中的全部 8 项职责:
    1. 入库适配器  2. 移除适配器  3. 列出适配器  4. 查询适配器
    5. 获取服务实例  6. 销毁服务实例  7. 错误标准化  8. 接口契约
    """

    async def install_adapter(self, model_id: str, adapter_content: str) -> LLMServiceInstance:
        """入库私有大模型 API 适配器并返回服务实例."""
        ...

    async def remove_adapter(self, model_id: str) -> bool:
        """移除已入库的适配器."""
        ...

    def list_adapters(self) -> list[dict]:
        """列出已入库的适配器清单."""
        ...

    def get_adapter_info(self, model_id: str) -> dict:
        """按大模型标识查询适配器元信息."""
        ...

    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:
        """获取大模型 API 调用服务实例."""
        ...

    async def destroy_service_instance(self, instance: LLMServiceInstance) -> bool:
        """销毁服务实例."""
        ...

    def standardize_error(self, exc: Exception) -> StandardizedLLMError:
        """将底层异常标准化为统一错误语义."""
        ...

    async def close_sessions(self) -> None: ...  # noqa: D102


LLMAdapterInterface = LLMAdapterLibInterface
