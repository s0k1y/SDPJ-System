"""Anthropic 格式适配器 — 支持 Anthropic Messages API"""
import aiohttp
from typing import Optional

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class AnthropicAdapter(LLMAdapter):
    """Anthropic Messages API 格式适配器"""

    def __init__(
        self,
        model_id: str,
        api_url: str,
        api_key: str,
        model_name: str | None = None,
        timeout: int = 60,
    ):
        self._model_id = model_id
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name or model_id
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def call(
        self,
        prompt: str,
        model_id: str,
        system_prompt: str = "",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> dict:
        actual_url = base_url or self._api_url
        actual_key = api_key or self._api_key
        actual_timeout = timeout or self._timeout

        if not actual_url.endswith("/messages"):
            url = f"{actual_url}/v1/messages"
        else:
            url = actual_url

        headers = {
            "x-api-key": actual_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self._model_name,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        if temperature > 0:
            payload["temperature"] = temperature

        try:
            session = self._get_session()
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=actual_timeout),
            ) as resp:
                data = await resp.json()
                if resp.status == 200:
                    content = data["content"][0]["text"]
                    return {
                        "success": True,
                        "content": content,
                        "model": data.get("model", self._model_name),
                        "usage": data.get("usage", {}),
                    }
                self._raise_api_error(resp.status, data)
        except StandardizedLLMError:
            raise
        except aiohttp.ServerTimeoutError as e:
            raise StandardizedLLMError(
                ErrorCategory.TIMEOUT, f"Request timed out ({actual_timeout}s)", original_error=e
            )
        except aiohttp.ClientError as e:
            raise StandardizedLLMError(
                ErrorCategory.NETWORK, str(e), original_error=e
            )
        except Exception as e:
            raise StandardizedLLMError(
                ErrorCategory.UNKNOWN, str(e), original_error=e
            )

    @staticmethod
    def _raise_api_error(status: int, data: dict) -> None:
        error_msg = data.get("error", {}).get("message", f"HTTP {status}")
        if status == 401:
            raise StandardizedLLMError(ErrorCategory.AUTH, error_msg, status_code=status)
        if status == 429:
            raise StandardizedLLMError(ErrorCategory.RATE_LIMIT, error_msg, status_code=status)
        if 400 <= status < 500:
            raise StandardizedLLMError(ErrorCategory.INVALID_REQUEST, error_msg, status_code=status)
        raise StandardizedLLMError(ErrorCategory.SERVER_ERROR, error_msg, status_code=status)

    def get_metadata(self) -> dict:
        return {
            "adapter_class": self.__class__.__name__,
            "model_id": self._model_id,
            "model_name": self._model_name,
            "api_url": self._api_url,
            "request_format": "anthropic",
        }
