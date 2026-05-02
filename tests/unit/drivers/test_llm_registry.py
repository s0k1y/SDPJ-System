"""
LLMRegistry 单元测试

测试覆盖:
1. 启动时批量注册已入库大模型
2. 查询已注册大模型清单
3. 按标识校验大模型是否可用
4. 注册用户上传的私有大模型
5. 注销用户移除的私有大模型
6. 关闭期批量销毁全部服务实例
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from sdpj.drivers.llm_registry import LLMRegistry
from sdpj.drivers.llm_registry_interface import ModelInfo
from sdpj.infrastructure.llm_adapters import (
    AdapterMetadata,
    LLMServiceInstance,
    AdapterValidationError,
    AdapterAlreadyExistsError,
    AdapterNotFoundError
)


class MockServiceInstance:
    """模拟服务实例"""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.closed = False

    async def call(self, prompt: str, **kwargs):
        return {"response": "mock response"}

    async def close(self):
        self.closed = True


@pytest.fixture
def mock_adapter_registry():
    """模拟 AdapterRegistry"""
    registry = AsyncMock()
    return registry


@pytest.fixture
def mock_utils_lib():
    """模拟 UtilsLib"""
    utils = MagicMock()
    return utils


@pytest.fixture
def llm_registry(mock_adapter_registry, mock_utils_lib):
    """创建 LLMRegistry 实例"""
    return LLMRegistry(
        adapter_registry=mock_adapter_registry,
        utils_lib=mock_utils_lib
    )


@pytest.mark.asyncio
class TestLLMRegistryInitialize:
    """测试启动时批量注册"""

    async def test_initialize_success(self, llm_registry, mock_adapter_registry):
        """测试成功批量注册已入库大模型"""
        # 准备测试数据
        metadata1 = AdapterMetadata(
            model_id="gpt-4",
            adapter_name="OpenAI GPT-4",
            version="1.0.0"
        )
        metadata2 = AdapterMetadata(
            model_id="claude-3",
            adapter_name="Anthropic Claude 3",
            version="1.0.0"
        )

        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")

        # 配置 mock
        mock_adapter_registry.list_adapters.return_value = [metadata1, metadata2]
        mock_adapter_registry.get_service_instance.side_effect = [service1, service2]

        # 执行测试
        result = await llm_registry.initialize()

        # 验证结果
        assert result is True
        assert len(llm_registry._registry) == 2
        assert "gpt-4" in llm_registry._registry
        assert "claude-3" in llm_registry._registry

    async def test_initialize_with_missing_instance(self, llm_registry, mock_adapter_registry):
        """测试批量注册时部分服务实例不存在"""
        # 准备测试数据
        metadata1 = AdapterMetadata(
            model_id="gpt-4",
            adapter_name="OpenAI GPT-4",
            version="1.0.0"
        )
        metadata2 = AdapterMetadata(
            model_id="claude-3",
            adapter_name="Anthropic Claude 3",
            version="1.0.0"
        )

        service1 = MockServiceInstance("gpt-4")

        # 配置 mock: 第二个适配器服务实例不存在
        mock_adapter_registry.list_adapters.return_value = [metadata1, metadata2]
        mock_adapter_registry.get_service_instance.side_effect = [
            service1,
            AdapterNotFoundError("服务实例未创建")
        ]

        # 执行测试
        result = await llm_registry.initialize()

        # 验证结果: 应该成功,但只注册了一个
        assert result is True
        assert len(llm_registry._registry) == 1
        assert "gpt-4" in llm_registry._registry

    async def test_initialize_failure(self, llm_registry, mock_adapter_registry):
        """测试批量注册失败"""
        # 配置 mock: 抛出异常
        mock_adapter_registry.list_adapters.side_effect = Exception("数据库错误")

        # 执行测试
        result = await llm_registry.initialize()

        # 验证结果
        assert result is False


@pytest.mark.asyncio
class TestLLMRegistryListModels:
    """测试查询已注册大模型清单"""

    async def test_list_registered_models_success(self, llm_registry, mock_adapter_registry):
        """测试成功查询已注册大模型清单"""
        # 准备测试数据
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        metadata1 = AdapterMetadata(
            model_id="gpt-4",
            adapter_name="OpenAI GPT-4",
            version="1.0.0",
            description="GPT-4 模型",
            supported_features=["chat", "completion"]
        )
        metadata2 = AdapterMetadata(
            model_id="claude-3",
            adapter_name="Anthropic Claude 3",
            version="1.0.0",
            description="Claude 3 模型",
            supported_features=["chat"]
        )

        # 配置 mock
        mock_adapter_registry.get_adapter_metadata.side_effect = [metadata1, metadata2]

        # 执行测试
        models = await llm_registry.list_registered_models()

        # 验证结果
        assert len(models) == 2
        assert isinstance(models[0], ModelInfo)
        assert models[0].model_id == "gpt-4"
        assert models[0].adapter_name == "OpenAI GPT-4"
        assert models[1].model_id == "claude-3"

    async def test_list_registered_models_empty(self, llm_registry):
        """测试查询空注册表"""
        # 执行测试
        models = await llm_registry.list_registered_models()

        # 验证结果
        assert len(models) == 0

    async def test_list_registered_models_with_missing_metadata(
        self,
        llm_registry,
        mock_adapter_registry
    ):
        """测试查询时部分元信息不存在"""
        # 准备测试数据
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        metadata1 = AdapterMetadata(
            model_id="gpt-4",
            adapter_name="OpenAI GPT-4",
            version="1.0.0"
        )

        # 配置 mock: 第二个元信息不存在
        mock_adapter_registry.get_adapter_metadata.side_effect = [
            metadata1,
            AdapterNotFoundError("元信息不存在")
        ]

        # 执行测试
        models = await llm_registry.list_registered_models()

        # 验证结果: 应该只返回一个
        assert len(models) == 1
        assert models[0].model_id == "gpt-4"


@pytest.mark.asyncio
class TestLLMRegistryIsModelAvailable:
    """测试按标识校验大模型是否可用"""

    async def test_is_model_available_true(self, llm_registry):
        """测试大模型可用"""
        # 准备测试数据
        service = MockServiceInstance("gpt-4")
        llm_registry._registry = {"gpt-4": service}

        # 执行测试
        is_available, instance = await llm_registry.is_model_available("gpt-4")

        # 验证结果
        assert is_available is True
        assert instance is service

    async def test_is_model_available_false(self, llm_registry):
        """测试大模型不可用"""
        # 执行测试
        is_available, instance = await llm_registry.is_model_available("gpt-4")

        # 验证结果
        assert is_available is False
        assert instance is None


@pytest.mark.asyncio
class TestLLMRegistryRegisterPrivateModel:
    """测试注册用户上传的私有大模型"""

    async def test_register_private_model_success(
        self,
        llm_registry,
        mock_adapter_registry,
        mock_utils_lib
    ):
        """测试成功注册私有大模型"""
        # 准备测试数据
        adapter_content = json.dumps({
            "adapter_name": "Custom GPT",
            "version": "1.0.0",
            "description": "自定义 GPT 模型",
            "supported_features": ["chat"]
        })
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)

        # 配置 mock
        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_adapter_registry.register_adapter.return_value = service

        # 执行测试
        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        # 验证结果
        assert success is True
        assert registered_id == model_id
        assert error == ""
        assert model_id in llm_registry._registry

    async def test_register_private_model_invalid_format(
        self,
        llm_registry,
        mock_utils_lib
    ):
        """测试文件格式校验失败"""
        # 准备测试数据
        adapter_content = "invalid json"
        model_id = "custom-gpt"

        # 配置 mock
        mock_utils_lib.validate_file_format.return_value = (False, "JSON 格式错误")

        # 执行测试
        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        # 验证结果
        assert success is False
        assert registered_id == ""
        assert "文件格式校验失败" in error

    async def test_register_private_model_validation_error(
        self,
        llm_registry,
        mock_adapter_registry,
        mock_utils_lib
    ):
        """测试适配器不符合规范"""
        # 准备测试数据
        adapter_content = json.dumps({
            "adapter_name": "Custom GPT",
            "version": "1.0.0"
        })
        model_id = "custom-gpt"

        # 配置 mock
        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_adapter_registry.register_adapter.side_effect = AdapterValidationError(
            "适配器不符合规范"
        )

        # 执行测试
        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        # 验证结果
        assert success is False
        assert registered_id == ""
        assert "适配器不符合规范" in error

    async def test_register_private_model_already_exists(
        self,
        llm_registry,
        mock_adapter_registry,
        mock_utils_lib
    ):
        """测试适配器已存在"""
        # 准备测试数据
        adapter_content = json.dumps({
            "adapter_name": "Custom GPT",
            "version": "1.0.0"
        })
        model_id = "custom-gpt"

        # 配置 mock
        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_adapter_registry.register_adapter.side_effect = AdapterAlreadyExistsError(
            "适配器已存在"
        )

        # 执行测试
        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        # 验证结果
        assert success is False
        assert registered_id == ""
        assert "适配器已存在" in error


@pytest.mark.asyncio
class TestLLMRegistryUnregisterPrivateModel:
    """测试注销用户移除的私有大模型"""

    async def test_unregister_private_model_success(
        self,
        llm_registry,
        mock_adapter_registry
    ):
        """测试成功注销私有大模型"""
        # 准备测试数据
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)
        llm_registry._registry = {model_id: service}

        # 配置 mock
        mock_adapter_registry.unregister_adapter.return_value = True

        # 执行测试
        success, error = await llm_registry.unregister_private_model(model_id)

        # 验证结果
        assert success is True
        assert error == ""
        assert model_id not in llm_registry._registry

    async def test_unregister_private_model_not_found(
        self,
        llm_registry,
        mock_adapter_registry
    ):
        """测试注销不存在的大模型"""
        # 准备测试数据
        model_id = "custom-gpt"

        # 配置 mock
        mock_adapter_registry.unregister_adapter.return_value = False

        # 执行测试
        success, error = await llm_registry.unregister_private_model(model_id)

        # 验证结果
        assert success is False
        assert "不存在" in error

    async def test_unregister_private_model_exception(
        self,
        llm_registry,
        mock_adapter_registry
    ):
        """测试注销时发生异常"""
        # 准备测试数据
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)
        llm_registry._registry = {model_id: service}

        # 配置 mock
        mock_adapter_registry.unregister_adapter.side_effect = Exception("数据库错误")

        # 执行测试
        success, error = await llm_registry.unregister_private_model(model_id)

        # 验证结果
        assert success is False
        assert "注销失败" in error


@pytest.mark.asyncio
class TestLLMRegistryShutdown:
    """测试关闭期批量销毁全部服务实例"""

    async def test_shutdown_success(self, llm_registry, mock_adapter_registry):
        """测试成功批量销毁服务实例"""
        # 准备测试数据
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        # 配置 mock
        mock_adapter_registry.destroy_service_instance.return_value = True

        # 执行测试
        result = await llm_registry.shutdown()

        # 验证结果
        assert result is True
        assert len(llm_registry._registry) == 0
        assert mock_adapter_registry.destroy_service_instance.call_count == 2

    async def test_shutdown_with_partial_failure(
        self,
        llm_registry,
        mock_adapter_registry
    ):
        """测试部分服务实例销毁失败"""
        # 准备测试数据
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        # 配置 mock: 第一个销毁失败,第二个成功
        mock_adapter_registry.destroy_service_instance.side_effect = [
            Exception("销毁失败"),
            True
        ]

        # 执行测试
        result = await llm_registry.shutdown()

        # 验证结果: 应该继续销毁其他实例并清空注册表
        assert result is True
        assert len(llm_registry._registry) == 0

    async def test_shutdown_empty_registry(self, llm_registry):
        """测试关闭空注册表"""
        # 执行测试
        result = await llm_registry.shutdown()

        # 验证结果
        assert result is True
        assert len(llm_registry._registry) == 0
