"""
SecureCommManager 接口定义

该模块定义了安全通信管理的接口契约。
"""
from __future__ import annotations

from typing import Protocol


class SecureCommManagerInterface(Protocol):
    """
    安全通信管理接口

    该接口定义了账号密码和配置文件的加密/解密能力，被 StateScheduler 调用。
    """

    def encrypt_credentials(self, plaintext: str) -> bytes:
        """
        对账号密码进行加密

        Args:
            plaintext: 明文账号密码

        Returns:
            密文（nonce + ciphertext）
        """
        ...

    def decrypt_credentials(self, ciphertext: bytes) -> str:
        """
        对账号密码进行解密

        Args:
            ciphertext: 密文形式的账号密码

        Returns:
            明文

        Raises:
            ValueError: 解密失败（密钥错误或密文被篡改）
        """
        ...

    def encrypt_config(self, plaintext: str | bytes) -> bytes:
        """
        对用户私有检测配置文件进行加密

        Args:
            plaintext: 明文形式的私有检测配置文件内容

        Returns:
            密文（nonce + ciphertext）
        """
        ...

    def decrypt_config(self, ciphertext: bytes) -> bytes:
        """
        对用户私有检测配置文件进行解密

        Args:
            ciphertext: 密文形式的私有检测配置文件内容

        Returns:
            明文

        Raises:
            ValueError: 解密失败（密钥错误或密文被篡改）
        """
        ...
