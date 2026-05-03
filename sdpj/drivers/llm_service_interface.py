"""LLMServiceInterface — 大模型服务接口

SDPJDetector 为唯一调用方 (符合 4.模型依赖关系图.puml 中 SDPJDetector → LLMService 边)。
"""
from typing import Protocol, Dict, Any, Optional

from sdpj.drivers.llm_types import LLMError, LLMServiceInstanceProtocol


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
