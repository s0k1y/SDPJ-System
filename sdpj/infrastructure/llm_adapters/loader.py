"""JSON 配置加载器 — 根据 request_format 创建对应适配器实例"""
import json
from pathlib import Path
from typing import Union

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import AdapterValidationError


def load_adapter_from_config(model_id: str, config: Union[dict, str, Path]) -> LLMAdapter:
    """根据 JSON 配置创建适配器实例

    Args:
        model_id: 大模型标识
        config: 配置字典、JSON 字符串或 JSON 文件路径

    Returns:
        对应 request_format 的适配器实例
    """
    if isinstance(config, (str, Path)):
        path = Path(config)
        if path.is_file():
            config = json.loads(path.read_text(encoding="utf-8"))
        else:
            config = json.loads(config)

    if not isinstance(config, dict):
        raise AdapterValidationError("config must be a dict or valid JSON")

    api_url = config.get("api_url") or config.get("base_url")
    api_key = config.get("api_key")
    if not api_url or not api_key:
        raise AdapterValidationError("config must contain 'api_url'/'base_url' and 'api_key'")

    request_format = config.get("request_format", "openai")
    model_name = config.get("model", model_id)
    timeout = config.get("timeout", 60)

    if request_format == "anthropic":
        from sdpj.infrastructure.llm_adapters.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(
            model_id=model_id,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
        )

    from sdpj.infrastructure.llm_adapters.openai_adapter import OpenAIAdapter
    return OpenAIAdapter(
        model_id=model_id,
        base_url=api_url.rstrip("/").removesuffix("/v1/chat/completions"),
        api_key=api_key,
        model_name=model_name,
        timeout=timeout,
    )
