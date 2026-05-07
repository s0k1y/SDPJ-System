"""JSON 配置加载器 — 根据 request_format 创建对应适配器实例"""
import json
from pathlib import Path
from typing import Union

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import AdapterValidationError


def load_adapter_from_config(model_id: str, config: Union[dict, str, Path]) -> LLMAdapter:
    """根据 JSON 配置创建适配器实例

    支持三种接入方式：
    1. 内置规范（OpenAI/Anthropic）：request_format="openai" 或 "anthropic"
    2. 系统抽象规范（自定义适配器）：request_format="custom" + adapter_class
    3. 扩展内置规范：为新的 API 格式添加新的内置适配器类

    Args:
        model_id: 大模型标识
        config: 配置字典、JSON 字符串或 JSON 文件路径

    Returns:
        对应 request_format 的适配器实例

    Raises:
        AdapterValidationError: 配置格式错误或缺少必需参数
    """
    if isinstance(config, (str, Path)):
        path = Path(config)
        if path.is_file():
            config = json.loads(path.read_text(encoding="utf-8"))
        else:
            config = json.loads(config)

    if not isinstance(config, dict):
        raise AdapterValidationError("config must be a dict or valid JSON")

    request_format = config.get("request_format", "openai")

    # 方式 2: 用户自定义适配器（系统抽象规范）
    if request_format == "custom":
        adapter_class_name = config.get("adapter_class")
        if not adapter_class_name:
            raise AdapterValidationError("custom adapter requires 'adapter_class' field")

        # 动态导入用户自定义适配器类
        try:
            module_name, class_name = adapter_class_name.rsplit(".", 1)
            import importlib
            module = importlib.import_module(module_name)
            adapter_class = getattr(module, class_name)

            # 验证是否继承自 LLMAdapter
            if not issubclass(adapter_class, LLMAdapter):
                raise AdapterValidationError(f"{adapter_class_name} must inherit from LLMAdapter")

            _META_KEYS = {"request_format", "adapter_class"}
            filtered_config = {k: v for k, v in config.items() if k not in _META_KEYS}
            return adapter_class(model_id=model_id, **filtered_config)
        except (ImportError, AttributeError, TypeError) as e:
            raise AdapterValidationError(f"Failed to load custom adapter: {e}")

    # 方式 1: 内置规范（OpenAI/Anthropic）
    api_url = (config.get("api_url") or config.get("base_url") or config.get("api_endpoint") or "").strip()
    api_key = (config.get("api_key") or "").strip()
    if not api_url or not api_key:
        raise AdapterValidationError("config must contain 'api_url'/'base_url'/'api_endpoint' and 'api_key'")

    model_name = config.get("model") or config.get("model_id") or model_id
    timeout = config.get("timeout", 60)

    if request_format == "anthropic":
        from sdpj.infrastructure.llm_adapters.anthropic_adapter import AnthropicAdapter
        clean_url = api_url.rstrip("/")
        clean_url = clean_url.removesuffix("/v1/messages").removesuffix("/messages")
        return AnthropicAdapter(
            model_id=model_id,
            api_url=clean_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
        )

    # 默认使用 OpenAI 兼容格式
    from sdpj.infrastructure.llm_adapters.openai_adapter import OpenAIAdapter
    return OpenAIAdapter(
        model_id=model_id,
        base_url=api_url.rstrip("/").removesuffix("/chat/completions"),
        api_key=api_key,
        model_name=model_name,
        timeout=timeout,
    )
