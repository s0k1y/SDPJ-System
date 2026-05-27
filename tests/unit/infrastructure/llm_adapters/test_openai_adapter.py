"""test_openai_adapter 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sdpj.infrastructure.llm_adapters.openai_adapter import OpenAIAdapter
from sdpj.infrastructure.llm_adapters.errors import StandardizedLLMError, ErrorCategory
from typing import Any


def make_adapter() -> None:
    """测试 make adapter."""
    return OpenAIAdapter("gpt-4", "https://api.openai.com", "sk-test")


def test_metadata_contains_model_id() -> None:
    """测试 test metadata contains model id."""
    assert make_adapter().get_metadata()["model_id"] == "gpt-4"


@pytest.mark.asyncio
async def test_call_success() -> None:
    """测试 test call success."""
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "ok"}}],
            "model": "gpt-4",
            "usage": {},
        }
    )
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await a.call("hi", "gpt-4")
    assert result["success"] and result["content"] == "ok"


@pytest.mark.asyncio
async def test_call_server_error() -> None:
    """测试 test call server error."""
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_resp.json = AsyncMock(return_value={})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(StandardizedLLMError) as exc:
            await a.call("hi", "gpt-4")
    assert exc.value.category == ErrorCategory.SERVER_ERROR
