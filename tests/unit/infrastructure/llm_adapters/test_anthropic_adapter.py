import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sdpj.infrastructure.llm_adapters.anthropic_adapter import AnthropicAdapter
from sdpj.infrastructure.llm_adapters.errors import StandardizedLLMError, ErrorCategory


def make_adapter():
    return AnthropicAdapter("claude-3", "https://api.anthropic.com", "sk-ant-test")


def test_metadata():
    m = make_adapter().get_metadata()
    assert m["model_id"] == "claude-3"
    assert m["request_format"] == "anthropic"


@pytest.mark.asyncio
async def test_call_success():
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "content": [{"type": "text", "text": "hello"}],
            "model": "claude-3",
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
        result = await a.call("hi", "claude-3")
    assert result["success"] and result["content"] == "hello"


@pytest.mark.asyncio
async def test_call_401_raises_auth_error():
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 401
    mock_resp.json = AsyncMock(return_value={"error": {"message": "unauthorized"}})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(StandardizedLLMError) as exc:
            await a.call("hi", "claude-3")
    assert exc.value.category == ErrorCategory.AUTH
