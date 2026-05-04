"""LLMServiceInterface — 大模型服务接口

SDPJDetector 为唯一调用方 (符合 4.模型依赖关系图.puml 中 SDPJDetector → LLMService 边)。
"""
from typing import Protocol, Dict, Any, Optional, runtime_checkable

from sdpj.infrastructure.llm_adapters.errors import LLMError


@runtime_checkable
class LLMServiceInstanceProtocol(Protocol):
    """LLM 服务实例协议"""
    model_id: str

    @property
    def active(self) -> bool: ...

    async def call(self, system_prompt: str, user_message: str, **kwargs: Any) -> dict: ...

    def destroy(self) -> None: ...


class LLMServiceInterface(Protocol):
    """大模型服务接口"""

    async def get_service_instance(self, model_id: str) -> LLMServiceInstanceProtocol: ...

    def assemble_request(
        self,
        system_prompt: str,
        user_message: str,
        call_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...

    async def invoke_llm(
        self,
        service_instance: LLMServiceInstanceProtocol,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]: ...

    def should_retry(self, error: LLMError, attempt: int) -> bool: ...

    def format_error_response(self, error: LLMError) -> Dict[str, Any]: ...
