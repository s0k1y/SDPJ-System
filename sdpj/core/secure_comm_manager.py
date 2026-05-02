"""
SecureCommManager 实现

该模块实现了安全通信管理的核心功能。
"""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .secure_comm_manager_interface import SecureCommManagerInterface


class SecureCommManager:
    """
    安全通信管理器

    负责账号密码和配置文件的加密/解密。
    使用 AES-256-GCM 算法，密钥内部维护。
    """

    def __init__(self, key: bytes | None = None):
        """
        初始化安全通信管理器

        Args:
            key: 可选的 256 位密钥（32 字节），如果不提供则自动生成
        """
        if key is None:
            # 生成 256 位随机密钥
            key = AESGCM.generate_key(bit_length=256)
        elif len(key) != 32:
            raise ValueError("密钥长度必须为 32 字节（256 位）")

        self._aesgcm = AESGCM(key)

    def encrypt_credentials(self, plaintext: str) -> bytes:
        """
        对账号密码进行加密

        Args:
            plaintext: 明文账号密码

        Returns:
            密文（nonce + ciphertext）
        """
        # 生成 12 字节随机 nonce
        nonce = os.urandom(12)

        # 加密
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        # 返回 nonce + ciphertext
        return nonce + ciphertext

    def decrypt_credentials(self, ciphertext: bytes) -> str:
        """
        对账号密码进行解密

        Args:
            ciphertext: 密文形式的账号密码

        Returns:
            明文

        Raises:
            ValueError: 解密失败
        """
        if len(ciphertext) < 12:
            raise ValueError("密文长度不足")

        # 提取 nonce（前 12 字节）
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]

        try:
            # 解密
            plaintext_bytes = self._aesgcm.decrypt(nonce, encrypted_data, None)
            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")

    def encrypt_config(self, plaintext: str | bytes) -> bytes:
        """
        对用户私有检测配置文件进行加密

        Args:
            plaintext: 明文形式的私有检测配置文件内容

        Returns:
            密文（nonce + ciphertext）
        """
        # 转换为 bytes
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode('utf-8')
        else:
            plaintext_bytes = plaintext

        # 生成 12 字节随机 nonce
        nonce = os.urandom(12)

        # 加密
        ciphertext = self._aesgcm.encrypt(nonce, plaintext_bytes, None)

        # 返回 nonce + ciphertext
        return nonce + ciphertext

    def decrypt_config(self, ciphertext: bytes) -> bytes:
        """
        对用户私有检测配置文件进行解密

        Args:
            ciphertext: 密文形式的私有检测配置文件内容

        Returns:
            明文

        Raises:
            ValueError: 解密失败
        """
        if len(ciphertext) < 12:
            raise ValueError("密文长度不足")

        # 提取 nonce（前 12 字节）
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]

        try:
            # 解密
            plaintext_bytes = self._aesgcm.decrypt(nonce, encrypted_data, None)
            return plaintext_bytes
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")
