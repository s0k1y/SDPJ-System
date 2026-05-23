"""LLMAdapter 抽象基类 — 所有适配器必须继承此类"""

from abc import ABC, abstractmethod

from sdpj.infrastructure.llm_adapters.errors import (
    ErrorCategory,
    StandardizedLLMError,
)


class LLMAdapter(ABC):
    """大模型 API 适配器基类

    适配器的核心职责是"向上抽象"：
    - 在构造时接收不同厂商的配置参数（api_key、base_url 等）
    - 将不同厂商的 API 格式转换为系统内部统一的调用接口
    - 向上层提供统一的 call() 方法，屏蔽底层 API 差异
    """

    def __init__(
        self,
        model_id: str,
        max_rps: float = 0.5,
        max_concurrency: int = 3,
    ):
        self._model_id = model_id
        self._max_rps = max_rps
        self._max_concurrency = max_concurrency

    @abstractmethod
    async def call(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> dict:
        """调用大模型 API（统一接口）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_tokens: 最大生成 token 数
            temperature: 温度参数（0.0-1.0）
            timeout: 请求超时时间（秒）

        Returns:
            成功: {"success": True, "content": str, "model": str, "usage": dict}
            失败: 抛出 StandardizedLLMError

        注意:
            - api_key、base_url、model_name 等配置参数在构造时已确定
            - 此方法只接收业务参数，不允许运行时覆盖配置
        """
        ...

    def get_metadata(self) -> dict:
        """返回适配器元信息"""
        return {
            "adapter_class": self.__class__.__name__,
            "module": self.__class__.__module__,
            "max_rps": self._max_rps,
            "max_concurrency": self._max_concurrency,
        }

    async def close(self) -> None:
        """关闭适配器，释放资源（如 HTTP 连接池）"""

    @staticmethod
    def _raise_api_error(
        status: int,
        error_msg: str,
        *,
        retry_after: str | None = None,
        extra_detail: dict | None = None,
    ) -> None:
        """统一的 API 错误抛出逻辑（子类复用）

        Args:
            status: HTTP 状态码
            error_msg: 错误消息
            retry_after: Retry-After 头值
            extra_detail: 额外的错误详情（如响应体）
        """
        detail: dict | None = None
        if retry_after is not None:
            try:
                detail = {"retry_after_seconds": float(retry_after)}
            except (ValueError, TypeError):
                detail = {"retry_after": retry_after}
        if extra_detail:
            detail = {**extra_detail, **(detail or {})} if detail else extra_detail

        if status == 401:
            raise StandardizedLLMError(
                ErrorCategory.AUTH, error_msg, status_code=status, detail=detail
            )
        if status == 429:
            raise StandardizedLLMError(
                ErrorCategory.RATE_LIMIT, error_msg, status_code=status, detail=detail
            )
        if 400 <= status < 500:
            raise StandardizedLLMError(
                ErrorCategory.INVALID_REQUEST, error_msg, status_code=status, detail=detail
            )
        raise StandardizedLLMError(
            ErrorCategory.SERVER_ERROR, error_msg, status_code=status, detail=detail
        )
