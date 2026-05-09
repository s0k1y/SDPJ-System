"""UtilsLib 加密工具"""

from cryptography.fernet import Fernet

from sdpj.infrastructure.utils.exceptions import EncryptionError


def symmetric_encrypt(plaintext: str, key: bytes) -> bytes:
    """对称加密"""
    try:
        f = Fernet(key)
        return f.encrypt(plaintext.encode("utf-8"))
    except Exception as e:
        raise EncryptionError(str(e)) from e


def symmetric_decrypt(ciphertext: bytes, key: bytes) -> str:
    """对称解密"""
    try:
        f = Fernet(key)
        return f.decrypt(ciphertext).decode("utf-8")
    except Exception as e:
        raise EncryptionError(str(e)) from e
