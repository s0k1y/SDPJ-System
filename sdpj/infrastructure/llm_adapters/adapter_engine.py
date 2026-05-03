"""通用 OpenAI 兼容格式适配器引擎"""
import aiohttp
from typing import Optional

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class OpenAICompatibleAdapter(LLMAdapter):
    """OpenAI 兼容格式的通用适配器

    支持所有遵循 OpenAI Chat Completions API 格式的大模型服务
    （DeepSeek、通义千问、Moonshot 等）。
    """

    def __init__(self, model_id: str, base_url: str, api_key: str, model_name: str | None = None):
        self._model_id = model_id
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name or model_id

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
        actual_base_url = base_url or self._base_url
        actual_api_key = api_key or self._api_key
        actual_model = self._model_name

        url = f"{actual_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {actual_api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": actual_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        content = data["choices"][0]["message"]["content"]
                        return {
                            "success": True,
                            "content": content,
                            "model": data.get("model", actual_model),
                            "usage": data.get("usage", {}),
                        }
                    self._raise_api_error(resp.status, data)
        except StandardizedLLMError:
            raise
        except aiohttp.ServerTimeoutError as e:
            raise StandardizedLLMError(
                ErrorCategory.TIMEOUT, f"Request timed out ({timeout}s)", original_error=e
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
        if status == 401:
            raise StandardizedLLMError(
                ErrorCategory.AUTH, "Authentication failed", status_code=status, detail=data
            )
        if status == 429:
            raise StandardizedLLMError(
                ErrorCategory.RATE_LIMIT, "Rate limit exceeded", status_code=status, detail=data
            )
        if 400 <= status < 500:
            raise StandardizedLLMError(
                ErrorCategory.INVALID_REQUEST,
                f"Client error {status}",
                status_code=status,
                detail=data,
            )
        raise StandardizedLLMError(
            ErrorCategory.SERVER_ERROR,
            f"Server error {status}",
            status_code=status,
            detail=data,
        )

    def get_metadata(self) -> dict:
        return {
            "adapter_class": self.__class__.__name__,
            "model_id": self._model_id,
            "model_name": self._model_name,
            "base_url": self._base_url,
        }
