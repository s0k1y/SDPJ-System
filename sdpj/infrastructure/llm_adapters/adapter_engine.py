"""通用 OpenAI 兼容格式适配器引擎"""
import aiohttp

from sdpj.infrastructure.llm_adapters.base import LLMAdapter
from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class OpenAICompatibleAdapter(LLMAdapter):
    """OpenAI 兼容格式的通用适配器

    支持所有遵循 OpenAI Chat Completions API 格式的大模型服务
    （DeepSeek、通义千问、Moonshot 等）。

    向上抽象职责：
    - 将 OpenAI 格式的配置参数（base_url、api_key、model）转换为统一的调用接口
    - 屏蔽 OpenAI API 的请求/响应格式细节
    - 提供统一的错误处理和超时控制
    """

    def __init__(self, model_id: str, base_url: str, api_key: str, model_name: str | None = None, max_rps: float = 0.5, max_concurrency: int = 3):
        super().__init__(model_id=model_id, max_rps=max_rps, max_concurrency=max_concurrency)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name or model_id
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
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> dict:
        """调用 OpenAI 兼容 API（统一接口）

        使用构造时配置的 base_url、api_key、model_name，
        不允许运行时覆盖配置参数。
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
                if resp.status == 200:
                    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                    return {
                        "success": True,
                        "content": content,
                        "model": data.get("model", self._model_name),
                        "usage": data.get("usage", {}),
                    }
                retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
                self._raise_api_error(resp.status, data, retry_after=retry_after)
        except StandardizedLLMError:
            raise
        except aiohttp.ServerTimeoutError as e:
            raise StandardizedLLMError(
                ErrorCategory.TIMEOUT, f"Request timed out ({timeout}s)", original_error=e
            )
        except aiohttp.ClientResponseError as e:
            self._raise_api_error(e.status, {}, retry_after=None)
        except aiohttp.ClientError as e:
            raise StandardizedLLMError(
                ErrorCategory.NETWORK, str(e), original_error=e
            )
        except Exception as e:
            raise StandardizedLLMError(
                ErrorCategory.UNKNOWN, str(e), original_error=e
            )

    @staticmethod
    def _raise_api_error(status: int, data: dict, *, retry_after: str | None = None) -> None:
        detail: dict | None = None
        if retry_after is not None:
            try:
                detail = {"retry_after_seconds": float(retry_after)}
            except (ValueError, TypeError):
                detail = {"retry_after": retry_after}
        if status == 401:
            raise StandardizedLLMError(
                ErrorCategory.AUTH, "Authentication failed", status_code=status, detail=detail
            )
        if status == 429:
            raise StandardizedLLMError(
                ErrorCategory.RATE_LIMIT, "Rate limit exceeded", status_code=status, detail=detail
            )
        if 400 <= status < 500:
            raise StandardizedLLMError(
                ErrorCategory.INVALID_REQUEST,
                f"Client error {status}",
                status_code=status,
                detail=detail or data,
            )
        raise StandardizedLLMError(
            ErrorCategory.SERVER_ERROR,
            f"Server error {status}",
            status_code=status,
            detail=detail or data,
        )

    def get_metadata(self) -> dict:
        return {
            **super().get_metadata(),
            "model_id": self._model_id,
            "model_name": self._model_name,
            "base_url": self._base_url,
        }
