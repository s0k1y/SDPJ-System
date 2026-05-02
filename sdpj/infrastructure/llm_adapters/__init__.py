"""LLM适配器库"""
from .llm_adapter_interface import LLMAdapterInterface
from .errors import (
    ErrorCategory,
    StandardizedLLMError,
    AdapterNotFoundError,
    LLMServiceInstance,
    AdapterValidationError,
    AdapterAlreadyExistsError
)

# 为了向后兼容,添加别名
AdapterMetadata = dict

__all__ = [
    'LLMAdapterInterface',
    'ErrorCategory',
    'StandardizedLLMError',
    'AdapterNotFoundError',
    'LLMServiceInstance',
    'AdapterMetadata',
    'AdapterValidationError',
    'AdapterAlreadyExistsError'
]
