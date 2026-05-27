"""Anthropic 格式适配器 — 支持 Anthropic Messages API."""

import aiohttp

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class AnthropicAdapter(LLMAdapter):
    """Anthropic Messages API 格式适配器.

    向上抽象职责:
    - 将 Anthropic 格式的配置参数(api_url,api_key,model)转换为统一的调用接口
    - 屏蔽 Anthropic API 的请求/响应格式细节(如 x-api-key header,messages 结构)
    - 提供统一的错误处理和超时控制
    """

    def __init__(  # noqa: D107, PLR0913
        self,
        model_id: str,
        api_url: str,
        api_key: str,
        model_name: str | None = None,
        timeout: int = 60,
        max_rps: float = 0.5,
        max_concurrency: int = 3,
    ) -> None:
        super().__init__(model_id=model_id, max_rps=max_rps, max_concurrency=max_concurrency)
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name or model_id
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:  # noqa: D102
        if self._session and not self._session.closed:
            await self._session.close()

    async def call(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,  # noqa: ASYNC109
    ) -> dict:
        """调用 Anthropic Messages API(统一接口).

        使用构造时配置的 api_url,api_key,model_name,
        不允许运行时覆盖配置参数.
        """
        if self._api_url.endswith("/messages"):
            url = self._api_url
        elif self._api_url.endswith("/v1"):
            url = f"{self._api_url}/messages"
        else:
            url = f"{self._api_url}/v1/messages"

        headers = {
            "x-api-key": self._api_key,
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
        if temperature >= 0:
            payload["temperature"] = temperature

        try:
            session = self._get_session()
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                data = await resp.json()
                if resp.status == 200:  # noqa: PLR2004
                    text_parts = [
                        block["text"]
                        for block in data.get("content", [])
                        if block.get("type") == "text"
                    ]
                    content = "\n".join(text_parts) if text_parts else ""
                    return {
                        "success": True,
                        "content": content,
                        "model": data.get("model", self._model_name),
                        "usage": data.get("usage", {}),
                    }
                retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
                error_msg = data.get("error", {}).get("message", f"HTTP {resp.status}")
                self._raise_api_error(resp.status, error_msg, retry_after=retry_after)
        except StandardizedLLMError:
            raise
        except aiohttp.ServerTimeoutError as e:
            raise StandardizedLLMError(  # noqa: B904
                ErrorCategory.TIMEOUT, f"Request timed out ({timeout}s)", original_error=e,
            )
        except aiohttp.ClientError as e:
            raise StandardizedLLMError(ErrorCategory.NETWORK, str(e), original_error=e)  # noqa: B904
        except Exception as e:  # noqa: BLE001
            raise StandardizedLLMError(ErrorCategory.UNKNOWN, str(e), original_error=e)  # noqa: B904

        return {}

    async def call_multimodal(  # noqa: D102
        self,
        system_prompt: str,
        content: list[dict],
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,  # noqa: ASYNC109
    ) -> dict:
        msg = "Anthropic 格式不支持多模态调用,请使用 OpenAI 兼容端点"
        raise NotImplementedError(msg)

    def get_metadata(self) -> dict:  # noqa: D102
        return {
            **super().get_metadata(),
            "model_id": self._model_id,
            "model_name": self._model_name,
            "api_url": self._api_url,
            "request_format": "anthropic",
        }
