"""test_llm_service 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sdpj.drivers.llm_service import LLMService
from sdpj.infrastructure.llm_adapters.errors import (
    StandardizedLLMError,
    ErrorCategory,
    LLMServiceInstance,
)
from typing import Any


def _make_service() -> None:
    """测试 make service."""
    adapter = MagicMock()
    utils = MagicMock()
    return LLMService(adapter, utils, max_retry_attempts=1, retry_wait_min=0, retry_wait_max=0)


def test_assemble_request_basic() -> None:
    """测试 test assemble request basic."""
    svc = _make_service()
    req = svc.assemble_request("sys", "user")
    assert req == {"system_prompt": "sys", "user_message": "user"}


def test_assemble_request_with_params() -> None:
    """测试 test assemble request with params."""
    svc = _make_service()
    req = svc.assemble_request("sys", "user", {"temperature": 0.5})
    assert req["temperature"] == 0.5


@pytest.mark.asyncio
async def test_get_service_instance_delegates() -> None:
    """测试 test get service instance delegates."""
    svc = _make_service()
    instance = MagicMock(spec=LLMServiceInstance)
    svc._llm_adapter.get_service_instance = AsyncMock(return_value=instance)
    result = await svc.get_service_instance("gpt-4")
    assert result is instance


@pytest.mark.asyncio
async def test_invoke_llm_success() -> None:
    """测试 test invoke llm success."""
    svc = _make_service()
    instance = MagicMock(spec=LLMServiceInstance)
    instance.call = AsyncMock(return_value={"text": "ok"})
    result = await svc.invoke_llm(instance, {"system_prompt": "s", "user_message": "u"})
    assert result == {"text": "ok"}


@pytest.mark.asyncio
async def test_invoke_llm_non_recoverable_raises() -> None:
    """测试 test invoke llm non recoverable raises."""
    svc = _make_service()
    instance = MagicMock(spec=LLMServiceInstance)
    err = StandardizedLLMError(category=ErrorCategory.AUTH, message="auth fail")
    instance.call = AsyncMock(side_effect=err)
    with pytest.raises(StandardizedLLMError):
        await svc.invoke_llm(instance, {"system_prompt": "s", "user_message": "u"})


@pytest.mark.asyncio
async def test_call_multimodal_delegates_to_instance() -> None:
    """call_multimodal 应委托到 service_instance.call_multimodal."""
    svc = _make_service()
    instance = MagicMock(spec=LLMServiceInstance)
    instance.call_multimodal = AsyncMock(return_value={"success": True, "content": "ok"})
    svc._llm_adapter.get_service_instance = AsyncMock(return_value=instance)

    content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}]
    result = await svc.call_multimodal("gpt-4", "sys", content)
    assert result["success"] is True
    instance.call_multimodal.assert_called_once_with("sys", content)


@pytest.mark.asyncio
async def test_call_multimodal_retries_on_rate_limit() -> None:
    """call_multimodal 触发 RATE_LIMIT 时应按指数退避重试."""
    svc = LLMService(
        llm_adapter=MagicMock(),
        utils=MagicMock(),
        max_retry_attempts=4,
        retry_wait_min=0,
        retry_wait_max=0,
    )
    instance = MagicMock(spec=LLMServiceInstance)
    rate_limit_err = StandardizedLLMError(category=ErrorCategory.RATE_LIMIT, message="rate limited")
    instance.call_multimodal = AsyncMock(
        side_effect=[rate_limit_err, rate_limit_err, rate_limit_err, {"success": True, "content": "ok"}],
    )
    svc._llm_adapter.get_service_instance = AsyncMock(return_value=instance)

    content = [{"type": "input_audio", "input_audio": {"data": "base64", "format": "wav"}}]
    result = await svc.call_multimodal("gpt-4", "", content)
    assert result["success"] is True
    assert instance.call_multimodal.call_count == 4
