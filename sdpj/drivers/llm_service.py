"""LLMService — 大模型服务接口实现.

职责:
1. 服务实例获取 - 按大模型标识获取调用服务实例
2. 单次调用入参装配 - 装配系统提示词,用户消息,可选参数
3. 发起大模型单次调用 - 执行单次独立调用并返回原始响应
4. 基于标准化错误的重试与退避决策 - 处理可恢复错误
5. 不可恢复错误的向上反馈 - 返回结构化错误结果
6. 将模型原始响应回传给调用方

依赖模块: LLMAdapterLib, UtilsLib
被依赖模块: SDPJDetector
"""

import asyncio
import time
from typing import Any, cast

from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    LLMServiceInstance,
    StandardizedLLMError,
)
from sdpj.infrastructure.llm_adapters.llm_adapter_interface import (
    LLMAdapterLibInterface,
)
from sdpj.infrastructure.utils.utils_interface import UtilsInterface


class LLMService:
    """大模型服务接口实现."""

    RECOVERABLE_CATEGORIES = {  # noqa: RUF012
        ErrorCategory.NETWORK,
        ErrorCategory.TIMEOUT,
        ErrorCategory.RATE_LIMIT,
    }

    def __init__(  # noqa: D107
        self,
        llm_adapter: LLMAdapterLibInterface,
        utils: UtilsInterface,
        max_retry_attempts: int = 5,
        retry_wait_min: int = 2,
        retry_wait_max: int = 60,
    ) -> None:
        self._llm_adapter = llm_adapter
        self._utils = utils
        self._max_retry_attempts = max_retry_attempts
        self._retry_wait_min = retry_wait_min
        self._retry_wait_max = retry_wait_max

    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:  # noqa: D102
        return await self._llm_adapter.get_service_instance(model_id)

    def assemble_request(  # noqa: D102
        self,
        system_prompt: str,
        user_message: str,
        call_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_data: dict[str, Any] = {
            "system_prompt": system_prompt,
            "user_message": user_message,
        }
        if call_params:
            request_data.update(call_params)
        return request_data

    async def invoke_llm(  # noqa: D102
        self,
        service_instance: LLMServiceInstance,
        request_data: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            return await self._invoke_with_retry(service_instance, request_data)
        except RetryError as e:
            last_exc = e.last_attempt.exception()
            if isinstance(last_exc, StandardizedLLMError):
                raise last_exc from e
            raise StandardizedLLMError(
                category=ErrorCategory.UNKNOWN,
                message=f"重试耗尽后仍失败: {e}",
                original_error=e,
            ) from e

    def _should_retry(self, retry_state) -> bool:  # noqa: ANN001
        if retry_state.outcome is None:
            return False
        exc = retry_state.outcome.exception()
        if isinstance(exc, StandardizedLLMError):
            return exc.category in self.RECOVERABLE_CATEGORIES
        return False

    async def _invoke_with_retry(
        self,
        service_instance: LLMServiceInstance,
        request_data: dict[str, Any],
    ) -> dict[str, Any]:
        @retry(
            stop=stop_after_attempt(self._max_retry_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self._retry_wait_min,
                max=self._retry_wait_max,
            ),
            retry=self._should_retry,
            reraise=True,
        )
        async def _do_call():  # noqa: ANN202
            try:
                system_prompt = request_data.get("system_prompt", "")
                user_message = request_data.get("user_message", "")
                extra = {
                    k: v
                    for k, v in request_data.items()
                    if k not in ("system_prompt", "user_message")
                }
                return await service_instance.call(system_prompt, user_message, **extra)
            except StandardizedLLMError:
                raise
            except TimeoutError as e:
                raise StandardizedLLMError(
                    category=ErrorCategory.TIMEOUT,
                    message=f"请求超时: {e}",
                    original_error=e,
                ) from e
            except Exception as e:
                raise StandardizedLLMError(
                    category=ErrorCategory.UNKNOWN,
                    message=f"未预期的错误: {e}",
                    original_error=e,
                ) from e

        return cast("dict[str, Any]", await _do_call())

    async def verify_connectivity(self, service_instance, timeout: float = 30.0) -> dict:  # noqa: ANN001, ASYNC109
        """验证模型连接性,发送健康检查消息并返回结构化结果."""
        req = self.assemble_request("", "Hello, respond with exactly: OK")
        start = time.monotonic()
        try:
            resp = await asyncio.wait_for(
                self.invoke_llm(service_instance, req),
                timeout=timeout,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": True,
                "status": "ok",
                "model": resp.get("model", ""),
                "latency_ms": latency_ms,
                "response_preview": resp.get("content", "")[:200],
            }
        except TimeoutError:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": False,
                "status": "timeout",
                "latency_ms": latency_ms,
                "error": f"验证超时({timeout}s)",
            }
        except StandardizedLLMError as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            category_map = {
                ErrorCategory.AUTH: "auth_failed",
                ErrorCategory.INVALID_REQUEST: "format_mismatch",
                ErrorCategory.NETWORK: "unreachable",
                ErrorCategory.TIMEOUT: "timeout",
            }
            status = category_map.get(e.category, "unknown_error")
            return {
                "success": False,
                "status": status,
                "latency_ms": latency_ms,
                "error": e.message,
            }
        except Exception as e:  # noqa: BLE001
            latency_ms = int((time.monotonic() - start) * 1000)
            err_msg = str(e)
            if "401" in err_msg or "auth" in err_msg.lower():
                status = "auth_failed"
            elif "404" in err_msg:
                status = "format_mismatch"
            elif "connect" in err_msg.lower() or "refused" in err_msg.lower():
                status = "unreachable"
            else:
                status = "unknown_error"
            return {
                "success": False,
                "status": status,
                "latency_ms": latency_ms,
                "error": err_msg,
            }

    def should_retry(self, error: StandardizedLLMError, attempt: int) -> bool:  # noqa: D102
        return error.category in self.RECOVERABLE_CATEGORIES and attempt < self._max_retry_attempts

    def format_error_response(self, error: StandardizedLLMError) -> dict[str, Any]:  # noqa: D102
        return {
            "success": False,
            "error": error.to_dict(),
            "response": None,
        }
