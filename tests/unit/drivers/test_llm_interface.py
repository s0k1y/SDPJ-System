"""
LLMInterface 单元测试

测试范围:
1. 服务实例获取
2. 单次调用入参装配
3. 发起大模型单次调用(含重试与错误处理)
4. 不可恢复错误的向上反馈

注意: 本测试独立定义所需类型,避免依赖模块的 Python 版本兼容性问题
"""

import pytest
from typing import Dict, Any
from enum import Enum


# ==================== 独立定义依赖类型 ====================

class ErrorCategory(Enum):
    """错误分类"""
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    PARAMETER_ERROR = "parameter_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    MODEL_ERROR = "model_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class StandardizedLLMError(Exception):
    """标准化的大模型调用错误"""

    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        original_error: Exception = None,
        details: Dict[str, Any] = None
    ):
        self.category = category
        self.message = message
        self.original_error = original_error
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class AdapterNotFoundError(Exception):
    """适配器未找到错误"""
    pass


# ==================== Mock 对象 ====================

class MockLLMServiceInstance:
    """Mock 大模型服务实例"""

    def __init__(self, response: Dict[str, Any] = None, error: Exception = None):
        self.response = response or {"content": "测试响应"}
        self.error = error
        self.call_count = 0

    async def call(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """模拟调用"""
        self.call_count += 1
        if self.error:
            raise self.error
        return self.response

    async def close(self):
        """模拟关闭"""
        pass


class MockLLMAdapter:
    """Mock LLMAdapterLib"""

    def __init__(self):
        self.instances: Dict[str, MockLLMServiceInstance] = {}

    async def get_service_instance(self, model_id: str):
        """模拟获取服务实例"""
        if model_id not in self.instances:
            raise AdapterNotFoundError(f"适配器 {model_id} 未找到")
        return self.instances[model_id]

    def register_instance(self, model_id: str, instance: MockLLMServiceInstance):
        """注册 mock 实例"""
        self.instances[model_id] = instance


class MockUtils:
    """Mock UtilsLib"""

    def serialize(self, data: Any, format: str) -> str:
        """模拟序列化"""
        import json
        return json.dumps(data)

    def deserialize(self, serialized_data: str, format: str) -> Any:
        """模拟反序列化"""
        import json
        return json.loads(serialized_data)


# ==================== 导入被测模块 ====================

# 需要先 patch 依赖模块,然后再导入
import sys
from unittest.mock import MagicMock

# 创建 mock 模块
mock_utils_interface = MagicMock()
mock_llm_adapter_interface = MagicMock()
mock_llm_adapter_errors = MagicMock()

# 设置 mock 模块的属性
mock_llm_adapter_errors.StandardizedLLMError = StandardizedLLMError
mock_llm_adapter_errors.ErrorCategory = ErrorCategory
mock_llm_adapter_errors.AdapterNotFoundError = AdapterNotFoundError

# 注入到 sys.modules
sys.modules['sdpj.infrastructure.utils.interface'] = mock_utils_interface
sys.modules['sdpj.infrastructure.llm_adapters.interface'] = mock_llm_adapter_interface
sys.modules['sdpj.infrastructure.llm_adapters.errors'] = mock_llm_adapter_errors

# 现在可以安全导入被测模块
from sdpj.drivers.llm_interface import LLMService


# ==================== Fixtures ====================

@pytest.fixture
def mock_llm_adapter():
    """创建 Mock LLMAdapter"""
    return MockLLMAdapter()


@pytest.fixture
def mock_utils():
    """创建 Mock Utils"""
    return MockUtils()


@pytest.fixture
def llm_service(mock_llm_adapter, mock_utils):
    """创建 LLMService 实例"""
    return LLMService(
        llm_adapter=mock_llm_adapter,
        utils=mock_utils,
        max_retry_attempts=3,
        retry_wait_min=1,
        retry_wait_max=10
    )


# ==================== 测试用例 ====================

class TestGetServiceInstance:
    """测试服务实例获取"""

    @pytest.mark.asyncio
    async def test_get_service_instance_success(self, llm_service, mock_llm_adapter):
        """测试成功获取服务实例"""
        # 准备
        model_id = "test-model"
        mock_instance = MockLLMServiceInstance()
        mock_llm_adapter.register_instance(model_id, mock_instance)

        # 执行
        instance = await llm_service.get_service_instance(model_id)

        # 验证
        assert instance is mock_instance

    @pytest.mark.asyncio
    async def test_get_service_instance_not_found(self, llm_service):
        """测试适配器未找到"""
        # 执行 & 验证
        with pytest.raises(AdapterNotFoundError):
            await llm_service.get_service_instance("non-existent-model")


class TestAssembleRequest:
    """测试单次调用入参装配"""

    def test_assemble_request_basic(self, llm_service):
        """测试基础入参装配"""
        # 准备
        system_prompt = "你是一个AI助手"
        user_message = "你好"

        # 执行
        request_data = llm_service.assemble_request(system_prompt, user_message)

        # 验证
        assert request_data["system_prompt"] == system_prompt
        assert request_data["user_message"] == user_message

    def test_assemble_request_with_params(self, llm_service):
        """测试带可选参数的入参装配"""
        # 准备
        system_prompt = "你是一个AI助手"
        user_message = "你好"
        call_params = {
            "temperature": 0.7,
            "max_tokens": 100
        }

        # 执行
        request_data = llm_service.assemble_request(
            system_prompt,
            user_message,
            call_params
        )

        # 验证
        assert request_data["system_prompt"] == system_prompt
        assert request_data["user_message"] == user_message
        assert request_data["temperature"] == 0.7
        assert request_data["max_tokens"] == 100

    def test_assemble_request_empty_params(self, llm_service):
        """测试空参数"""
        # 准备
        system_prompt = ""
        user_message = "测试消息"

        # 执行
        request_data = llm_service.assemble_request(system_prompt, user_message)

        # 验证
        assert request_data["system_prompt"] == ""
        assert request_data["user_message"] == "测试消息"


class TestInvokeLLM:
    """测试发起大模型单次调用"""

    @pytest.mark.asyncio
    async def test_invoke_llm_success(self, llm_service):
        """测试成功调用"""
        # 准备
        expected_response = {"content": "成功响应", "tokens": 10}
        mock_instance = MockLLMServiceInstance(response=expected_response)
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好"
        }

        # 执行
        response = await llm_service.invoke_llm(mock_instance, request_data)

        # 验证
        assert response == expected_response
        assert mock_instance.call_count == 1

    @pytest.mark.asyncio
    async def test_invoke_llm_with_params(self, llm_service):
        """测试带参数的调用"""
        # 准备
        expected_response = {"content": "成功响应"}
        mock_instance = MockLLMServiceInstance(response=expected_response)
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好",
            "temperature": 0.8,
            "max_tokens": 200
        }

        # 执行
        response = await llm_service.invoke_llm(mock_instance, request_data)

        # 验证
        assert response == expected_response

    @pytest.mark.asyncio
    async def test_invoke_llm_non_recoverable_error(self, llm_service):
        """测试不可恢复错误(不重试)"""
        # 准备
        auth_error = StandardizedLLMError(
            category=ErrorCategory.AUTH_ERROR,
            message="鉴权失败"
        )
        mock_instance = MockLLMServiceInstance(error=auth_error)
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好"
        }

        # 执行 & 验证
        with pytest.raises(StandardizedLLMError) as exc_info:
            await llm_service.invoke_llm(mock_instance, request_data)

        assert exc_info.value.category == ErrorCategory.AUTH_ERROR
        # 不可恢复错误应该只调用一次,不重试
        assert mock_instance.call_count == 1

    @pytest.mark.asyncio
    async def test_invoke_llm_recoverable_error_with_retry(self, llm_service):
        """测试可恢复错误(会重试)"""
        # 准备
        network_error = StandardizedLLMError(
            category=ErrorCategory.NETWORK_ERROR,
            message="网络错误"
        )
        mock_instance = MockLLMServiceInstance(error=network_error)
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好"
        }

        # 执行 & 验证
        with pytest.raises(StandardizedLLMError) as exc_info:
            await llm_service.invoke_llm(mock_instance, request_data)

        assert exc_info.value.category == ErrorCategory.NETWORK_ERROR
        # 可恢复错误应该重试 max_retry_attempts 次
        assert mock_instance.call_count == 3

    @pytest.mark.asyncio
    async def test_invoke_llm_retry_success_on_second_attempt(self, llm_service):
        """测试第二次重试成功"""
        # 准备
        class RetryableInstance:
            def __init__(self):
                self.call_count = 0
                self.success_response = {"content": "成功"}

            async def call(self, prompt: str, **kwargs):
                self.call_count += 1
                if self.call_count == 1:
                    # 第一次调用失败
                    raise StandardizedLLMError(
                        category=ErrorCategory.TIMEOUT_ERROR,
                        message="超时"
                    )
                # 第二次调用成功
                return self.success_response

            async def close(self):
                pass

        mock_instance = RetryableInstance()
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好"
        }

        # 执行
        response = await llm_service.invoke_llm(mock_instance, request_data)

        # 验证
        assert response == {"content": "成功"}
        assert mock_instance.call_count == 2

    @pytest.mark.asyncio
    async def test_invoke_llm_unknown_error(self, llm_service):
        """测试未预期的错误"""
        # 准备
        unknown_error = ValueError("未知错误")
        mock_instance = MockLLMServiceInstance(error=unknown_error)
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": "你好"
        }

        # 执行 & 验证
        with pytest.raises(StandardizedLLMError) as exc_info:
            await llm_service.invoke_llm(mock_instance, request_data)

        assert exc_info.value.category == ErrorCategory.UNKNOWN_ERROR
        assert "未预期的错误" in exc_info.value.message


class TestFormatErrorResponse:
    """测试不可恢复错误的向上反馈"""

    def test_format_error_response(self, llm_service):
        """测试错误响应格式化"""
        # 准备
        error = StandardizedLLMError(
            category=ErrorCategory.AUTH_ERROR,
            message="鉴权失败",
            details={"code": 401}
        )

        # 执行
        error_response = llm_service.format_error_response(error)

        # 验证
        assert error_response["success"] is False
        assert error_response["response"] is None
        assert error_response["error"]["category"] == "auth_error"
        assert error_response["error"]["message"] == "鉴权失败"
        assert error_response["error"]["details"]["code"] == 401

    def test_format_error_response_with_original_error(self, llm_service):
        """测试包含原始错误的错误响应"""
        # 准备
        original_error = ValueError("原始错误")
        error = StandardizedLLMError(
            category=ErrorCategory.MODEL_ERROR,
            message="模型错误",
            original_error=original_error
        )

        # 执行
        error_response = llm_service.format_error_response(error)

        # 验证
        assert error_response["success"] is False
        assert error_response["error"]["category"] == "model_error"
        assert "原始错误" in error_response["error"]["original_error"]


class TestLLMServiceInterface:
    """测试 LLMServiceInterface 协议"""

    def test_llm_service_implements_interface(self, llm_service):
        """测试 LLMService 实现了 LLMServiceInterface"""
        # 验证所有接口方法都存在
        assert hasattr(llm_service, "get_service_instance")
        assert hasattr(llm_service, "assemble_request")
        assert hasattr(llm_service, "invoke_llm")
        assert hasattr(llm_service, "format_error_response")

        # 验证方法可调用
        assert callable(llm_service.get_service_instance)
        assert callable(llm_service.assemble_request)
        assert callable(llm_service.invoke_llm)
        assert callable(llm_service.format_error_response)


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_empty_system_prompt(self, llm_service):
        """测试空系统提示词"""
        # 准备
        mock_instance = MockLLMServiceInstance()
        request_data = {
            "system_prompt": "",
            "user_message": "你好"
        }

        # 执行
        response = await llm_service.invoke_llm(mock_instance, request_data)

        # 验证
        assert response is not None

    @pytest.mark.asyncio
    async def test_empty_user_message(self, llm_service):
        """测试空用户消息"""
        # 准备
        mock_instance = MockLLMServiceInstance()
        request_data = {
            "system_prompt": "你是AI助手",
            "user_message": ""
        }

        # 执行
        response = await llm_service.invoke_llm(mock_instance, request_data)

        # 验证
        assert response is not None

    def test_assemble_request_params_override(self, llm_service):
        """测试参数覆盖"""
        # 准备
        system_prompt = "你是AI助手"
        user_message = "你好"
        call_params = {
            "system_prompt": "不应该覆盖",  # 会覆盖基础参数
            "temperature": 0.9
        }

        # 执行
        request_data = llm_service.assemble_request(
            system_prompt,
            user_message,
            call_params
        )

        # 验证 - call_params 会覆盖基础参数
        assert request_data["system_prompt"] == "不应该覆盖"
        assert request_data["temperature"] == 0.9
