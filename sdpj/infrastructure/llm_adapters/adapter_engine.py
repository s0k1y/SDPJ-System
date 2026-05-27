"""通用 OpenAI 兼容格式适配器引擎."""

import aiohttp

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class OpenAICompatibleAdapter(LLMAdapter):
    """OpenAI 兼容格式的通用适配器.

    支持所有遵循 OpenAI Chat Completions API 格式的大模型服务
    (DeepSeek,通义千问,Moonshot 等).

    向上抽象职责:
    - 将 OpenAI 格式的配置参数(base_url,api_key,model)转换为统一的调用接口
    - 屏蔽 OpenAI API 的请求/响应格式细节
    - 提供统一的错误处理和超时控制
    """

    def __init__(  # noqa: D107, PLR0913
        self,
        model_id: str,
        base_url: str,
        api_key: str,
        model_name: str | None = None,
        max_rps: float = 0.5,
        max_concurrency: int = 3,
    ) -> None:
        super().__init__(model_id=model_id, max_rps=max_rps, max_concurrency=max_concurrency)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name or model_id
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
        """调用 OpenAI 兼容 API(统一接口).

        使用构造时配置的 base_url,api_key,model_name,
        不允许运行时覆盖配置参数.
        """
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

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
                    content = (data.get("choices") or [{}])[0].get("message", {}).get(
                        "content",
                    ) or ""
                    return {
                        "success": True,
                        "content": content,
                        "model": data.get("model", self._model_name),
                        "usage": data.get("usage", {}),
                    }
                retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
                if resp.status == 401:  # noqa: PLR2004
                    error_msg = "Authentication failed"
                elif resp.status == 429:  # noqa: PLR2004
                    error_msg = "Rate limit exceeded"
                elif 400 <= resp.status < 500:  # noqa: PLR2004
                    error_msg = f"Client error {resp.status}"
                else:
                    error_msg = f"Server error {resp.status}"
                self._raise_api_error(
                    resp.status, error_msg, retry_after=retry_after, extra_detail=data,
                )
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

    def get_metadata(self) -> dict:  # noqa: D102
        return {
            **super().get_metadata(),
            "model_id": self._model_id,
            "model_name": self._model_name,
            "base_url": self._base_url,
        }
