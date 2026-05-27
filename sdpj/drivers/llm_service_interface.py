"""LLMServiceInterface — 大模型服务接口.

SDPJDetector 为唯一调用方 (符合 4.模型依赖关系图.puml 中 SDPJDetector → LLMService 边).
"""

from typing import Any, Protocol, runtime_checkable

from sdpj.infrastructure.llm_adapters.errors import LLMError


@runtime_checkable
class LLMServiceInstanceProtocol(Protocol):
    """LLM 服务实例协议."""

    model_id: str

    @property
    def active(self) -> bool: ...  # noqa: D102

    async def call(self, system_prompt: str, user_message: str, **kwargs: Any) -> dict: ...  # noqa: ANN401, D102

    async def call_multimodal(self, system_prompt: str, content: list[dict], **kwargs: Any) -> dict: ...  # noqa: ANN401, D102

    def destroy(self) -> None: ...  # noqa: D102


class LLMServiceInterface(Protocol):
    """大模型服务接口."""

    async def get_service_instance(self, model_id: str) -> LLMServiceInstanceProtocol: ...  # noqa: D102

    def assemble_request(  # noqa: D102
        self,
        system_prompt: str,
        user_message: str,
        call_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def invoke_llm(  # noqa: D102
        self,
        service_instance: LLMServiceInstanceProtocol,
        request_data: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def call_multimodal(  # noqa: D102
        self,
        model_id: str,
        system_prompt: str,
        content: list[dict[str, Any]],
    ) -> dict[str, Any]: ...

    def should_retry(self, error: LLMError, attempt: int) -> bool: ...  # noqa: D102

    def format_error_response(self, error: LLMError) -> dict[str, Any]: ...  # noqa: D102

    async def verify_connectivity(self, service_instance, timeout: float = 30.0) -> dict:  # noqa: ANN001, ASYNC109
        """验证模型连接性,发送健康检查消息并返回结构化结果  # noqa: "latency_ms": int, "model": str, "response_preview": str}.  # noqa: E501, "status": str, D205        返回: {"success": bool, D210, E501, E501.        """
        ...
