import pytest
from sdpj.infrastructure.llm_adapters.loader import load_adapter_from_config
from sdpj.infrastructure.llm_adapters.errors import AdapterValidationError


VALID_OPENAI = {
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-test",
    "request_format": "openai",
}
VALID_ANTHROPIC = {
    "api_url": "https://api.anthropic.com",
    "api_key": "sk-ant-test",
    "request_format": "anthropic",
}


def test_load_openai_adapter():
    from sdpj.infrastructure.llm_adapters.openai_adapter import OpenAIAdapter

    adapter = load_adapter_from_config("gpt-4", VALID_OPENAI)
    assert isinstance(adapter, OpenAIAdapter)


def test_load_anthropic_adapter():
    from sdpj.infrastructure.llm_adapters.anthropic_adapter import AnthropicAdapter

    adapter = load_adapter_from_config("claude-3", VALID_ANTHROPIC)
    assert isinstance(adapter, AnthropicAdapter)


def test_missing_api_url_raises():
    with pytest.raises(AdapterValidationError):
        load_adapter_from_config("m", {"api_key": "k"})


def test_missing_api_key_raises():
    with pytest.raises(AdapterValidationError):
        load_adapter_from_config("m", {"api_url": "https://example.com"})


def test_load_from_json_string():
    import json
    from sdpj.infrastructure.llm_adapters.openai_adapter import OpenAIAdapter

    adapter = load_adapter_from_config("gpt-4", json.dumps(VALID_OPENAI))
    assert isinstance(adapter, OpenAIAdapter)


def test_invalid_config_type_raises():
    with pytest.raises(AdapterValidationError):
        load_adapter_from_config("m", 123)


def test_zhipu_glm_url_construction():
    adapter = load_adapter_from_config(
        "glm-4-flash",
        {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "test-key",
            "request_format": "openai",
            "model": "glm-4-flash",
        },
    )
    assert adapter._base_url == "https://open.bigmodel.cn/api/paas/v4"


def test_openai_url_construction():
    adapter = load_adapter_from_config(
        "gpt-4",
        {
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-test",
            "request_format": "openai",
        },
    )
    assert adapter._base_url == "https://api.openai.com/v1"


def test_full_url_strips_chat_completions():
    adapter = load_adapter_from_config(
        "gpt-4",
        {
            "api_url": "https://api.openai.com/v1/chat/completions",
            "api_key": "sk-test",
            "request_format": "openai",
        },
    )
    assert adapter._base_url == "https://api.openai.com/v1"
