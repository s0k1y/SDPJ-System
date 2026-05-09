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
from unittest.mock import AsyncMock, MagicMock

from sdpj.drivers.llm_registry import LLMRegistry
from sdpj.drivers.llm_registry_interface import ModelInfo
from sdpj.infrastructure.llm_adapters.errors import (
    LLMServiceInstance,
    AdapterValidationError,
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
)


class MockServiceInstance:
    """模拟服务实例"""

    def __init__(self, model_id: str, active: bool = True):
        self.model_id = model_id
        self._active = active
        self.closed = False

    @property
    def active(self) -> bool:
        return self._active

    async def call(self, prompt: str, **kwargs):
        return {"response": "mock response"}

    async def close(self):
        self.closed = True


@pytest.fixture
def mock_adapter_lib():
    """模拟 LLMAdapterLib"""
    lib = MagicMock()
    lib.get_service_instance = AsyncMock()
    lib.install_adapter = AsyncMock()
    lib.remove_adapter = AsyncMock()
    return lib


@pytest.fixture
def mock_utils_lib():
    """模拟 UtilsLib"""
    utils = MagicMock()
    return utils


@pytest.fixture
def llm_registry(mock_adapter_lib, mock_utils_lib):
    """创建 LLMRegistry 实例"""
    return LLMRegistry(
        adapter_lib=mock_adapter_lib,
        utils_lib=mock_utils_lib
    )


@pytest.mark.asyncio
class TestLLMRegistryInitialize:
    """测试启动时批量注册"""

    async def test_initialize_success(self, llm_registry, mock_adapter_lib):
        """测试成功批量注册已入库大模型"""
        metadata1 = {"model_id": "gpt-4", "adapter_name": "OpenAI GPT-4", "version": "1.0.0"}
        metadata2 = {"model_id": "claude-3", "adapter_name": "Anthropic Claude 3", "version": "1.0.0"}

        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")

        mock_adapter_lib.list_adapters.return_value = [metadata1, metadata2]
        mock_adapter_lib.get_service_instance.side_effect = [service1, service2]

        result = await llm_registry.initialize()

        assert result is True
        assert len(llm_registry._registry) == 2
        assert "gpt-4" in llm_registry._registry
        assert "claude-3" in llm_registry._registry

    async def test_initialize_with_missing_instance(self, llm_registry, mock_adapter_lib):
        """测试批量注册时部分服务实例不存在"""
        metadata1 = {"model_id": "gpt-4", "adapter_name": "OpenAI GPT-4", "version": "1.0.0"}
        metadata2 = {"model_id": "claude-3", "adapter_name": "Anthropic Claude 3", "version": "1.0.0"}

        service1 = MockServiceInstance("gpt-4")

        mock_adapter_lib.list_adapters.return_value = [metadata1, metadata2]
        mock_adapter_lib.get_service_instance.side_effect = [
            service1,
            AdapterNotFoundError("服务实例未创建")
        ]

        result = await llm_registry.initialize()

        assert result is False
        assert "gpt-4" in llm_registry._registry

    async def test_initialize_failure(self, llm_registry, mock_adapter_lib):
        """测试批量注册失败"""
        mock_adapter_lib.list_adapters.side_effect = Exception("数据库错误")

        result = await llm_registry.initialize()

        assert result is False


@pytest.mark.asyncio
class TestLLMRegistryListModels:
    """测试查询已注册大模型清单"""

    async def test_list_registered_models_success(self, llm_registry, mock_adapter_lib):
        """测试成功查询已注册大模型清单"""
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        metadata1 = {
            "model_id": "gpt-4",
            "adapter_name": "OpenAI GPT-4",
            "version": "1.0.0",
            "description": "GPT-4 模型",
            "supported_features": ["chat", "completion"]
        }
        metadata2 = {
            "model_id": "claude-3",
            "adapter_name": "Anthropic Claude 3",
            "version": "1.0.0",
            "description": "Claude 3 模型",
            "supported_features": ["chat"]
        }

        mock_adapter_lib.get_adapter_info.side_effect = [metadata1, metadata2]

        models = await llm_registry.list_registered_models()

        assert len(models) == 2
        assert isinstance(models[0], ModelInfo)

    async def test_list_registered_models_empty(self, llm_registry):
        """测试查询空注册表"""
        models = await llm_registry.list_registered_models()
        assert len(models) == 0

    async def test_list_registered_models_with_missing_metadata(
        self, llm_registry, mock_adapter_lib
    ):
        """测试查询时部分元信息不存在"""
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {
            "gpt-4": service1,
            "claude-3": service2
        }

        metadata1 = {
            "model_id": "gpt-4",
            "adapter_name": "OpenAI GPT-4",
            "version": "1.0.0"
        }

        mock_adapter_lib.get_adapter_info.side_effect = [
            metadata1,
            AdapterNotFoundError("元信息不存在")
        ]

        models = await llm_registry.list_registered_models()

        assert len(models) == 2
        unknown_model = [m for m in models if m.adapter_name == "unknown"]
        assert len(unknown_model) == 1


@pytest.mark.asyncio
class TestLLMRegistryIsModelAvailable:
    """测试按标识校验大模型是否可用"""

    async def test_is_model_available_true(self, llm_registry):
        """测试大模型可用"""
        service = MockServiceInstance("gpt-4")
        llm_registry._registry = {"gpt-4": service}

        is_available, instance = await llm_registry.is_model_available("gpt-4")

        assert is_available is True
        assert instance is service

    async def test_is_model_available_false(self, llm_registry):
        """测试大模型不可用"""
        is_available, instance = await llm_registry.is_model_available("gpt-4")

        assert is_available is False
        assert instance is None

    async def test_is_model_available_inactive(self, llm_registry):
        """测试大模型实例已失活"""
        service = MockServiceInstance("gpt-4", active=False)
        llm_registry._registry = {"gpt-4": service}

        is_available, instance = await llm_registry.is_model_available("gpt-4")

        assert is_available is False
        assert instance is None


@pytest.mark.asyncio
class TestLLMRegistryRegisterPrivateModel:
    """测试注册用户上传的私有大模型"""

    async def test_register_private_model_success(
        self, llm_registry, mock_adapter_lib, mock_utils_lib
    ):
        """测试成功注册私有大模型"""
        adapter_content = json.dumps({
            "adapter_name": "Custom GPT",
            "version": "1.0.0",
            "description": "自定义 GPT 模型",
            "supported_features": ["chat"]
        })
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)

        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_utils_lib.deserialize_json.return_value = json.loads(adapter_content)
        mock_adapter_lib.install_adapter.return_value = service

        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        assert success is True
        assert registered_id == model_id
        assert error == ""
        assert model_id in llm_registry._registry

    async def test_register_private_model_invalid_format(
        self, llm_registry, mock_utils_lib
    ):
        """测试文件格式校验失败"""
        adapter_content = "invalid json"
        model_id = "custom-gpt"

        mock_utils_lib.validate_file_format.return_value = (False, "JSON 格式错误")

        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        assert success is False
        assert registered_id == ""
        assert "格式" in error or "校验" in error

    async def test_register_private_model_validation_error(
        self, llm_registry, mock_adapter_lib, mock_utils_lib
    ):
        """测试适配器不符合规范"""
        adapter_content = json.dumps({"adapter_name": "Custom GPT", "version": "1.0.0"})
        model_id = "custom-gpt"

        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_utils_lib.deserialize_json.return_value = json.loads(adapter_content)
        mock_adapter_lib.install_adapter.side_effect = AdapterValidationError("适配器不符合规范")

        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        assert success is False
        assert registered_id == ""
        assert "校验" in error or "适配器" in error

    async def test_register_private_model_already_exists(
        self, llm_registry, mock_adapter_lib, mock_utils_lib
    ):
        """测试适配器已存在"""
        adapter_content = json.dumps({"adapter_name": "Custom GPT", "version": "1.0.0"})
        model_id = "custom-gpt"

        mock_utils_lib.validate_file_format.return_value = (True, "")
        mock_utils_lib.deserialize_json.return_value = json.loads(adapter_content)
        mock_adapter_lib.install_adapter.side_effect = AdapterAlreadyExistsError("适配器已存在")

        success, registered_id, error = await llm_registry.register_private_model(
            adapter_content=adapter_content,
            model_id=model_id
        )

        assert success is False
        assert registered_id == ""
        assert "已存在" in error


@pytest.mark.asyncio
class TestLLMRegistryUnregisterPrivateModel:
    """测试注销用户移除的私有大模型"""

    async def test_unregister_private_model_success(
        self, llm_registry, mock_adapter_lib
    ):
        """测试成功注销私有大模型"""
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)
        llm_registry._registry = {model_id: service}

        success, error = await llm_registry.unregister_private_model(model_id)

        assert success is True
        assert error == ""
        assert model_id not in llm_registry._registry

    async def test_unregister_private_model_not_found(self, llm_registry):
        """测试注销不存在的大模型"""
        success, error = await llm_registry.unregister_private_model("custom-gpt")

        assert success is False
        assert "未注册" in error

    async def test_unregister_private_model_exception(
        self, llm_registry, mock_adapter_lib
    ):
        """测试注销时发生异常"""
        model_id = "custom-gpt"
        service = MockServiceInstance(model_id)
        llm_registry._registry = {model_id: service}

        mock_adapter_lib.remove_adapter.side_effect = Exception("数据库错误")

        success, error = await llm_registry.unregister_private_model(model_id)

        assert success is False
        assert "注销失败" in error


@pytest.mark.asyncio
class TestLLMRegistryShutdown:
    """测试关闭期批量销毁全部服务实例"""

    async def test_shutdown_success(self, llm_registry, mock_adapter_lib):
        """测试成功批量销毁服务实例"""
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {"gpt-4": service1, "claude-3": service2}

        result = await llm_registry.shutdown()

        assert result is True
        assert len(llm_registry._registry) == 0
        assert mock_adapter_lib.destroy_service_instance.call_count == 2

    async def test_shutdown_with_partial_failure(self, llm_registry, mock_adapter_lib):
        """测试部分服务实例销毁失败"""
        service1 = MockServiceInstance("gpt-4")
        service2 = MockServiceInstance("claude-3")
        llm_registry._registry = {"gpt-4": service1, "claude-3": service2}

        mock_adapter_lib.destroy_service_instance.side_effect = [
            Exception("销毁失败"),
            True
        ]

        result = await llm_registry.shutdown()

        assert result is True
        assert len(llm_registry._registry) == 0

    async def test_shutdown_empty_registry(self, llm_registry):
        """测试关闭空注册表"""
        result = await llm_registry.shutdown()

        assert result is True
        assert len(llm_registry._registry) == 0
