"""OpenAI 格式适配器 — 支持所有 OpenAI Chat Completions API 兼容服务"""
from sdpj.infrastructure.llm_adapters.adapter_engine import OpenAICompatibleAdapter


class OpenAIAdapter(OpenAICompatibleAdapter):
    """OpenAI API 格式适配器

    支持 OpenAI、DeepSeek、通义千问、Moonshot 等遵循
    OpenAI Chat Completions API 格式的大模型服务。
    """

    def __init__(
        self,
        model_id: str,
        base_url: str,
        api_key: str,
        model_name: str | None = None,
        timeout: int = 60,
    ):
        super().__init__(
            model_id=model_id,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )
        self._timeout = timeout
