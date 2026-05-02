"""
LLMInterface - 大模型服务接口模块

职责:
1. 服务实例获取 - 按大模型标识获取调用服务实例
2. 单次调用入参装配 - 装配系统提示词、用户消息、可选参数
3. 发起大模型单次调用 - 执行单次独立调用并返回原始响应
4. 基于标准化错误的重试与退避决策 - 处理可恢复错误
5. 不可恢复错误的向上反馈 - 返回结构化错误结果
6. 将模型原始响应回传给调用方

不负责: 维护多轮对话历史、入库/销毁适配器、记录API调用日志、
        鉴权凭据持久化、响应内容业务语义解析、编码/多模态还原

依赖模块: LLMAdapterLib, UtilsLib
被依赖模块: SDPJDetector
"""

from typing import Protocol, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    RetryError
)

from sdpj.infrastructure.llm_adapters.llm_adapter_interface import LLMAdapterInterface
from sdpj.infrastructure.llm_adapters.errors import (
    StandardizedLLMError,
    ErrorCategory,
    AdapterNotFoundError,
    LLMServiceInstance
)
from sdpj.infrastructure.utils.utils_interface import UtilsInterface


class LLMServiceInterface(Protocol):
    """大模型服务接口 - 对外暴露的统一接口"""

    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:
        """
        按大模型标识获取调用服务实例

        Args:
            model_id: 目标大模型标识

        Returns:
            LLMServiceInstance: 可直接发起调用的大模型 API 调用服务实例句柄

        Raises:
            AdapterNotFoundError: 对应适配器尚未入库时透传下层的明确错误

        触发场景:
            SDPJDetector 在一次大模型调用前的前置步骤
        """
        ...

    def assemble_request(
        self,
        system_prompt: str,
        user_message: str,
        call_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        单次调用入参装配

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            call_params: 可选调用参数(如temperature, max_tokens等)

        Returns:
            Dict[str, Any]: 适配器可消费的单次请求数据

        触发场景:
            SDPJDetector 在每轮样本注入前拼装单次请求

        不负责的边界:
            不维护多轮对话历史(API调用无记忆性,每次调用视为全新独立对话)
        """
        ...

    async def invoke_llm(
        self,
        service_instance: LLMServiceInstance,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发起大模型单次调用(带重试与错误处理)

        Args:
            service_instance: 服务实例句柄
            request_data: 装配后的单次请求数据

        Returns:
            Dict[str, Any]: 大模型原始响应

        Raises:
            StandardizedLLMError: 不可恢复错误或重试耗尽后的错误

        触发场景:
            SDPJDetector 对每条样本完成一次独立注入并读取响应

        不负责的边界:
            不在调用间保留任何上下文或会话状态
        """
        ...

    def format_error_response(self, error: StandardizedLLMError) -> Dict[str, Any]:
        """
        不可恢复错误的向上反馈

        Args:
            error: LLMAdapterLib 已做标准化的错误

        Returns:
            Dict[str, Any]: 向上返回的结构化错误结果

        触发场景:
            经过重试策略判定后仍无法完成调用,或错误分类本身不可恢复
        """
        ...


class LLMService:
    """大模型服务接口实现"""

    # 可恢复错误类别(需要重试)
    RECOVERABLE_ERROR_CATEGORIES = {
        ErrorCategory.NETWORK_ERROR,
        ErrorCategory.TIMEOUT_ERROR,
        ErrorCategory.RATE_LIMIT_ERROR
    }

    # 不可恢复错误类别(直接返回)
    NON_RECOVERABLE_ERROR_CATEGORIES = {
        ErrorCategory.AUTH_ERROR,
        ErrorCategory.PARAMETER_ERROR,
        ErrorCategory.MODEL_ERROR,
        ErrorCategory.UNKNOWN_ERROR
    }

    def __init__(
        self,
        llm_adapter: LLMAdapterInterface,
        utils: UtilsInterface,
        max_retry_attempts: int = 3,
        retry_wait_min: int = 1,
        retry_wait_max: int = 10
    ):
        """
        初始化大模型服务

        Args:
            llm_adapter: LLMAdapterLib 实例
            utils: UtilsLib 实例
            max_retry_attempts: 最大重试次数(默认3次)
            retry_wait_min: 重试最小等待时间(秒,默认1秒)
            retry_wait_max: 重试最大等待时间(秒,默认10秒)
        """
        self._llm_adapter = llm_adapter
        self._utils = utils
        self._max_retry_attempts = max_retry_attempts
        self._retry_wait_min = retry_wait_min
        self._retry_wait_max = retry_wait_max

    async def get_service_instance(self, model_id: str) -> LLMServiceInstance:
        """
        按大模型标识获取调用服务实例

        Args:
            model_id: 目标大模型标识

        Returns:
            LLMServiceInstance: 可直接发起调用的大模型 API 调用服务实例句柄

        Raises:
            AdapterNotFoundError: 对应适配器尚未入库时透传下层的明确错误
        """
        # 直接调用 LLMAdapterLib 的获取服务实例方法
        return await self._llm_adapter.get_service_instance(model_id)

    def assemble_request(
        self,
        system_prompt: str,
        user_message: str,
        call_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        单次调用入参装配

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            call_params: 可选调用参数

        Returns:
            Dict[str, Any]: 适配器可消费的单次请求数据
        """
        # 构建基础请求数据
        request_data = {
            "system_prompt": system_prompt,
            "user_message": user_message
        }

        # 合并可选调用参数
        if call_params:
            request_data.update(call_params)

        return request_data

    async def invoke_llm(
        self,
        service_instance: LLMServiceInstance,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发起大模型单次调用(带重试与错误处理)

        Args:
            service_instance: 服务实例句柄
            request_data: 装配后的单次请求数据

        Returns:
            Dict[str, Any]: 大模型原始响应

        Raises:
            StandardizedLLMError: 不可恢复错误或重试耗尽后的错误
        """
        try:
            # 使用 tenacity 进行重试
            response = await self._invoke_with_retry(service_instance, request_data)
            return response
        except RetryError as e:
            # 重试耗尽,提取原始错误
            if isinstance(e.last_attempt.exception(), StandardizedLLMError):
                raise e.last_attempt.exception()
            else:
                # 未预期的错误,包装为 UNKNOWN_ERROR
                raise StandardizedLLMError(
                    category=ErrorCategory.UNKNOWN_ERROR,
                    message=f"重试耗尽后仍失败: {str(e)}",
                    original_error=e
                )

    def _should_retry(self, retry_state) -> bool:
        """
        判断是否应该重试

        Args:
            retry_state: tenacity 的 RetryCallState 对象

        Returns:
            bool: 是否应该重试
        """
        # 获取异常
        if retry_state.outcome is None:
            return False

        exception = retry_state.outcome.exception()
        if exception is None:
            return False

        if isinstance(exception, StandardizedLLMError):
            # 只对可恢复错误进行重试
            return exception.category in self.RECOVERABLE_ERROR_CATEGORIES
        return False

    async def _invoke_with_retry(
        self,
        service_instance: LLMServiceInstance,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        带重试的调用实现

        Args:
            service_instance: 服务实例句柄
            request_data: 装配后的单次请求数据

        Returns:
            Dict[str, Any]: 大模型原始响应

        Raises:
            StandardizedLLMError: 标准化后的错误
        """
        @retry(
            stop=stop_after_attempt(self._max_retry_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self._retry_wait_min,
                max=self._retry_wait_max
            ),
            retry=self._should_retry,
            reraise=True
        )
        async def _call_with_error_handling():
            try:
                # 提取 prompt 和其他参数
                system_prompt = request_data.get("system_prompt", "")
                user_message = request_data.get("user_message", "")

                # 组合完整 prompt
                full_prompt = f"{system_prompt}\n\n{user_message}".strip()

                # 提取其他调用参数
                call_kwargs = {
                    k: v for k, v in request_data.items()
                    if k not in ["system_prompt", "user_message"]
                }

                # 调用服务实例
                response = await service_instance.call(full_prompt, **call_kwargs)
                return response

            except StandardizedLLMError as e:
                # 已标准化的错误,直接抛出(由 retry 装饰器判断是否重试)
                raise
            except Exception as e:
                # 未标准化的错误,包装为 UNKNOWN_ERROR
                standardized_error = StandardizedLLMError(
                    category=ErrorCategory.UNKNOWN_ERROR,
                    message=f"未预期的错误: {str(e)}",
                    original_error=e
                )
                raise standardized_error

        return await _call_with_error_handling()

    def format_error_response(self, error: StandardizedLLMError) -> Dict[str, Any]:
        """
        不可恢复错误的向上反馈

        Args:
            error: LLMAdapterLib 已做标准化的错误

        Returns:
            Dict[str, Any]: 向上返回的结构化错误结果
        """
        return {
            "success": False,
            "error": error.to_dict(),
            "response": None
        }
