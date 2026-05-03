"""LLMAdapter 抽象基类 — 所有适配器必须继承此类"""
from abc import ABC, abstractmethod
from typing import Optional


class LLMAdapter(ABC):
    """大模型 API 适配器基类

    用户编写的私有适配器必须继承此类并实现 call() 方法。
    """

    @abstractmethod
    async def call(
        self,
        prompt: str,
        model_id: str,
        system_prompt: str = "",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> dict:
        """调用大模型 API

        Returns:
            成功: {"success": True, "content": str, "model": str, "usage": dict}
            失败: 抛出 StandardizedLLMError
        """
        ...

    def get_metadata(self) -> dict:
        """返回适配器元信息"""
        return {
            "adapter_class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }
