"""LLM 适配器错误定义与服务实例."""

from enum import Enum
from typing import Any, cast


class LLMError(Exception):
    """LLM 错误基类."""


class ErrorCategory(Enum):
    """标准化错误分类(对应规格职责 7)."""

    NETWORK = "network_error"
    AUTH = "auth_error"
    RATE_LIMIT = "rate_limit_error"
    INVALID_REQUEST = "invalid_request_error"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout_error"
    UNKNOWN = "unknown_error"


class StandardizedLLMError(LLMError):
    """标准化 LLM 错误,包装底层异常并提供统一语义."""

    def __init__(  # noqa: D107
        self,
        category: ErrorCategory,
        message: str,
        original_error: Exception | None = None,
        status_code: int | None = None,
        detail: Any = None,  # noqa: ANN401
    ) -> None:
        self.category = category
        # 空消息防护:避免日志和下游丢失错误上下文
        if not message or not message.strip():
            if original_error is not None:
                message = f"{category.value}: {type(original_error).__name__}({original_error!r})"
            elif status_code is not None:
                message = f"{category.value}: HTTP {status_code}"
            else:
                message = f"{category.value}: (no detail available)"
        self.message = message
        self.original_error = original_error
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:  # noqa: D102
        result = {
            "error": self.category.value,
            "message": self.message,
        }
        if self.status_code is not None:
            result["status_code"] = self.status_code  # type: ignore[assignment]
        if self.detail is not None:
            result["detail"] = self.detail
        return result


class AdapterNotFoundError(Exception):
    """适配器未找到."""


class AdapterValidationError(Exception):
    """适配器校验失败."""


class AdapterAlreadyExistsError(Exception):
    """同标识适配器已存在."""


class LLMServiceInstance:
    """LLM API 调用服务实例(对应规格职责 5/6)."""

    def __init__(self, model_id: str, adapter: Any) -> None:  # noqa: ANN401, D107
        self.model_id = model_id
        self.adapter = adapter
        self._active = True

    @property
    def active(self) -> bool:  # noqa: D102
        return self._active

    async def call(self, system_prompt: str, user_message: str, **kwargs) -> dict:  # noqa: ANN003, D102
        if not self._active:
            msg = f"Service instance for '{self.model_id}' has been destroyed"
            raise RuntimeError(msg)
        adapter_kwargs = {k: v for k, v in kwargs.items() if k != "model_id"}
        return cast("dict", await self.adapter.call(
            prompt=user_message,
            system_prompt=system_prompt,
            **adapter_kwargs,
        ))

    async def call_multimodal(self, system_prompt: str, content: list[dict], **kwargs) -> dict:  # noqa: ANN003, D102
        if not self._active:
            msg = f"Service instance for '{self.model_id}' has been destroyed"
            raise RuntimeError(msg)
        return cast("dict", await self.adapter.call_multimodal(
            system_prompt=system_prompt,
            content=content,
            **kwargs,
        ))

    async def destroy(self) -> None:  # noqa: D102
        self._active = False
        if self.adapter is not None:
            await self.adapter.close()
        self.adapter = None
