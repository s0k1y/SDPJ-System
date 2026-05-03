"""LLM 适配器错误定义与服务实例"""
from enum import Enum
from typing import Any

from sdpj.drivers.llm_types import LLMError


class ErrorCategory(Enum):
    """标准化错误分类（对应规格职责 7）"""
    NETWORK = "network_error"
    AUTH = "auth_error"
    RATE_LIMIT = "rate_limit_error"
    INVALID_REQUEST = "invalid_request_error"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout_error"
    UNKNOWN = "unknown_error"


class StandardizedLLMError(LLMError):
    """标准化 LLM 错误，包装底层异常并提供统一语义"""

    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        original_error: Exception | None = None,
        status_code: int | None = None,
        detail: Any = None,
    ):
        self.category = category
        self.message = message
        self.original_error = original_error
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)

    def to_dict(self) -> dict:
        result = {
            "error": self.category.value,
            "message": self.message,
        }
        if self.status_code is not None:
            result["status_code"] = self.status_code
        if self.detail is not None:
            result["detail"] = self.detail
        return result


class AdapterNotFoundError(Exception):
    """适配器未找到"""
    pass


class AdapterValidationError(Exception):
    """适配器校验失败"""
    pass


class AdapterAlreadyExistsError(Exception):
    """同标识适配器已存在"""
    pass


class LLMServiceInstance:
    """LLM API 调用服务实例（对应规格职责 5/6）"""

    def __init__(self, model_id: str, adapter: Any):
        self.model_id = model_id
        self.adapter = adapter
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    async def call(self, system_prompt: str, user_message: str, **kwargs) -> dict:
        if not self._active:
            raise RuntimeError(f"Service instance for '{self.model_id}' has been destroyed")
        return await self.adapter.call(
            prompt=user_message,
            model_id=self.model_id,
            system_prompt=system_prompt,
            **kwargs,
        )

    def destroy(self) -> None:
        self._active = False
        self.adapter = None
