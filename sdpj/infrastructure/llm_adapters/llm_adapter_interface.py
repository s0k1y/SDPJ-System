"""LLM Adapter 接口定义"""
from typing import Protocol, Optional, List


class LLMAdapterInterface(Protocol):
    """大模型适配器接口"""

    async def call(
        self,
        system_prompt: str,
        user_message: str,
        images: Optional[List[str]] = None,
        audios: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """调用大模型

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            images: 图片列表
            audios: 音频列表
            videos: 视频列表
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        ...
