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
