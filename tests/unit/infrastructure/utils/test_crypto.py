"""test_crypto 模块单元测试."""

import pytest
from cryptography.fernet import Fernet
from sdpj.infrastructure.utils.crypto import symmetric_encrypt, symmetric_decrypt
from typing import Any


def test_encrypt_decrypt_roundtrip() -> None:
    """测试 test encrypt decrypt roundtrip."""
    key = Fernet.generate_key()
    assert symmetric_decrypt(symmetric_encrypt("hello", key), key) == "hello"


def test_encrypt_produces_different_ciphertext() -> None:
    """测试 test encrypt produces different ciphertext."""
    key = Fernet.generate_key()
    assert symmetric_encrypt("hello", key) != symmetric_encrypt("hello", key)


def test_decrypt_wrong_key_raises() -> None:
    """测试 test decrypt wrong key raises."""
    key1, key2 = Fernet.generate_key(), Fernet.generate_key()
    with pytest.raises(Exception):
        symmetric_decrypt(symmetric_encrypt("hello", key1), key2)


def test_encrypt_unicode() -> None:
    """测试 test encrypt unicode."""
    key = Fernet.generate_key()
    text = "你好世界"
    assert symmetric_decrypt(symmetric_encrypt(text, key), key) == text
