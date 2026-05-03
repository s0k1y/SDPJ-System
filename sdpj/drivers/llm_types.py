"""Drivers 层 LLM 契约类型"""
from typing import Protocol, Any, runtime_checkable


class LLMError(Exception):
    """LLM 错误基类"""
    pass


@runtime_checkable
class LLMServiceInstanceProtocol(Protocol):
    """LLM 服务实例协议"""
    model_id: str

    @property
    def active(self) -> bool: ...

    async def call(self, system_prompt: str, user_message: str, **kwargs: Any) -> dict: ...

    def destroy(self) -> None: ...
