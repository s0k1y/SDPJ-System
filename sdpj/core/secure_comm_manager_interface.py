"""
SecureCommManager 接口定义

该模块定义了安全通信管理的接口契约。
"""
from __future__ import annotations

from typing import Protocol


class SecureCommManagerInterface(Protocol):
    """安全通信管理接口，被 StateScheduler 调用。"""

    def encrypt_credentials(self, plaintext: str) -> bytes: ...

    def decrypt_credentials(self, ciphertext: bytes) -> str: ...

    def get_public_key_spki_b64(self) -> str: ...

    def decrypt_from_client(self, ciphertext: bytes) -> str: ...
