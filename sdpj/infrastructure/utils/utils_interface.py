"""UtilsLib 接口定义"""
from typing import Protocol


class UtilsInterface(Protocol):
    """工具库接口"""

    def base64_encode(self, text: str) -> str:
        """Base64编码

        Args:
            text: 原始文本

        Returns:
            编码后的字符串
        """
        ...

    def base64_decode(self, encoded: str) -> str:
        """Base64解码

        Args:
            encoded: 编码后的字符串

        Returns:
            原始文本
        """
        ...

    def url_encode(self, text: str) -> str:
        """URL编码

        Args:
            text: 原始文本

        Returns:
            编码后的字符串
        """
        ...

    def url_decode(self, encoded: str) -> str:
        """URL解码

        Args:
            encoded: 编码后的字符串

        Returns:
            原始文本
        """
        ...

    def hash_password(self, password: str) -> str:
        """密码哈希

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        ...

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            hashed: 哈希后的密码

        Returns:
            验证成功返回True
        """
        ...
