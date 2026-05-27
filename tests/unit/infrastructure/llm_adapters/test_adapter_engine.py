"""test_adapter_engine 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sdpj.infrastructure.llm_adapters.adapter_engine import OpenAICompatibleAdapter
from sdpj.infrastructure.llm_adapters.errors import StandardizedLLMError, ErrorCategory
from typing import Any


def make_adapter() -> None:
    """测试 make adapter."""
    return OpenAICompatibleAdapter("gpt-4", "https://api.openai.com", "sk-test")


def test_get_metadata() -> None:
    """测试 test get metadata."""
    a = make_adapter()
    m = a.get_metadata()
    assert m["model_id"] == "gpt-4"
    assert m["base_url"] == "https://api.openai.com"


def test_url_construction_openai() -> None:
    """测试 test url construction openai."""
    a = OpenAICompatibleAdapter("gpt-4", "https://api.openai.com/v1", "sk-test")
    assert a._base_url == "https://api.openai.com/v1"


def test_url_construction_zhipu() -> None:
    """测试 test url construction zhipu."""
    a = OpenAICompatibleAdapter("glm-4-flash", "https://open.bigmodel.cn/api/paas/v4", "test-key")
    assert a._base_url == "https://open.bigmodel.cn/api/paas/v4"


@pytest.mark.asyncio
async def test_call_success() -> None:
    """测试 test call success."""
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "hello"}}],
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
    assert result["success"] and result["content"] == "hello"


@pytest.mark.asyncio
async def test_call_401_raises_auth_error() -> None:
    """测试 test call 401 raises auth error."""
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 401
    mock_resp.json = AsyncMock(return_value={"error": "unauthorized"})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(StandardizedLLMError) as exc:
            await a.call("hi", "gpt-4")
    assert exc.value.category == ErrorCategory.AUTH


@pytest.mark.asyncio
async def test_call_429_raises_rate_limit() -> None:
    """测试 test call 429 raises rate limit."""
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 429
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
    assert exc.value.category == ErrorCategory.RATE_LIMIT


@pytest.mark.asyncio
async def test_call_multimodal_assembles_content_array() -> None:
    """call_multimodal 应将 content 数组组装为 messages 并 POST."""
    a = make_adapter()
    captured_payload: list[dict] = []

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "image description"}}],
            "model": "gpt-4",
            "usage": {},
        },
    )
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    def capture_post(url, json, headers, timeout):  # noqa: ANN001
        captured_payload.append(json)
        return mock_resp

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=capture_post)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    content = [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123"}},
        {"type": "text", "text": "describe this image"},
    ]

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await a.call_multimodal("", content)

    assert result["success"] is True
    assert result["content"] == "image description"
    assert len(captured_payload) == 1
    messages = captured_payload[0]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == content


@pytest.mark.asyncio
async def test_call_multimodal_with_system_prompt() -> None:
    """call_multimodal 带 system_prompt 时应组装 system + user 两条消息."""
    a = make_adapter()
    captured_payload: list[dict] = []

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "ok"}}],
            "model": "gpt-4",
            "usage": {},
        },
    )
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    def capture_post(url, json, headers, timeout):  # noqa: ANN001
        captured_payload.append(json)
        return mock_resp

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=capture_post)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    content = [{"type": "input_audio", "input_audio": {"data": "base64data", "format": "mp3"}}]

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await a.call_multimodal("system msg", content)

    messages = captured_payload[0]["messages"]
    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": "system msg"}
    assert messages[1] == {"role": "user", "content": content}
