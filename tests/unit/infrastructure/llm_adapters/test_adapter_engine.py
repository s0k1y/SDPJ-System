import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sdpj.infrastructure.llm_adapters.adapter_engine import OpenAICompatibleAdapter
from sdpj.infrastructure.llm_adapters.errors import StandardizedLLMError, ErrorCategory


def make_adapter():
    return OpenAICompatibleAdapter("gpt-4", "https://api.openai.com", "sk-test")


def test_get_metadata():
    a = make_adapter()
    m = a.get_metadata()
    assert m["model_id"] == "gpt-4"
    assert m["base_url"] == "https://api.openai.com"


@pytest.mark.asyncio
async def test_call_success():
    a = make_adapter()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "choices": [{"message": {"content": "hello"}}],
        "model": "gpt-4",
        "usage": {},
    })
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
async def test_call_401_raises_auth_error():
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
async def test_call_429_raises_rate_limit():
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
