"""
抽象驱动层 (Abstract Driver Layer)

提供以下模块:
- DataProcessor: 检测数据处理
- LLMService: 大模型服务接口
- LLMRegistry: 大模型注册中心
- UserCenter: 用户管理中心
"""

from .data_processor_interface import DataProcessorInterface
from .data_processor import DataProcessor
from .llm_service_interface import LLMServiceInterface
from .llm_service import LLMService
from .llm_registry_interface import LLMRegistryInterface, ModelInfo
from .llm_registry import LLMRegistry
from .user_center_interface import UserCenterInterface
from .user_center import UserCenter

__all__ = [
    "DataProcessorInterface",
    "DataProcessor",
    "LLMServiceInterface",
    "LLMService",
    "LLMRegistryInterface",
    "ModelInfo",
    "LLMRegistry",
    "UserCenterInterface",
    "UserCenter",
]
