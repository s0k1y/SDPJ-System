"""LLM适配器错误定义"""
from enum import Enum


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class StandardizedLLMError(Exception):
    """标准化LLM错误"""
    
    def __init__(self, category: ErrorCategory, message: str):
        self.category = category
        self.message = message
        super().__init__(message)


class AdapterNotFoundError(Exception):
    """适配器未找到错误"""
    pass


class LLMServiceInstance:
    """LLM服务实例"""
    
    def __init__(self, adapter_id: str, adapter):
        self.adapter_id = adapter_id
        self.adapter = adapter
    
    async def call(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """调用LLM"""
        return await self.adapter.call(system_prompt, user_message, **kwargs)


class AdapterValidationError(Exception):
    """适配器验证错误"""
    pass


class AdapterAlreadyExistsError(Exception):
    """适配器已存在错误"""
    pass
