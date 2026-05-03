import pytest
from cryptography.fernet import Fernet
from sdpj.infrastructure.utils.crypto import symmetric_encrypt, symmetric_decrypt


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key()
    assert symmetric_decrypt(symmetric_encrypt("hello", key), key) == "hello"


def test_encrypt_produces_different_ciphertext():
    key = Fernet.generate_key()
    assert symmetric_encrypt("hello", key) != symmetric_encrypt("hello", key)


def test_decrypt_wrong_key_raises():
    key1, key2 = Fernet.generate_key(), Fernet.generate_key()
    with pytest.raises(Exception):
        symmetric_decrypt(symmetric_encrypt("hello", key1), key2)


def test_encrypt_unicode():
    key = Fernet.generate_key()
    text = "你好世界"
    assert symmetric_decrypt(symmetric_encrypt(text, key), key) == text
