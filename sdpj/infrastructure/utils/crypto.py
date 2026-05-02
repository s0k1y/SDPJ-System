"""UtilsLib 加密工具"""
from cryptography.fernet import Fernet
import bcrypt


def symmetric_encrypt(plaintext: str, key: bytes) -> bytes:
    """对称加密"""
    f = Fernet(key)
    return f.encrypt(plaintext.encode('utf-8'))


def symmetric_decrypt(ciphertext: bytes, key: bytes) -> str:
    """对称解密"""
    f = Fernet(key)
    return f.decrypt(ciphertext).decode('utf-8')


def generate_key() -> bytes:
    """生成对称密钥"""
    return Fernet.generate_key()


def hash_password(password: str, salt: bytes = None) -> bytes:
    """密码哈希"""
    if salt is None:
        salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)


def verify_password(password: str, hashed: bytes) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
