"""
SecureCommManager 单元测试
"""
import json

import pytest

from sdpj.core.secure_comm_manager import SecureCommManager


class TestCredentialsEncryption:
    """测试账号密码加密"""

    def test_encrypt_credentials_success(self):
        """测试成功加密账号密码"""
        manager = SecureCommManager()
        plaintext = "password123"

        ciphertext = manager.encrypt_credentials(plaintext)

        assert ciphertext is not None
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 12  # nonce (12) + encrypted data

    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        manager = SecureCommManager()
        ciphertext = manager.encrypt_credentials("")

        assert ciphertext is not None
        assert len(ciphertext) >= 12

    def test_encrypt_special_characters(self):
        """测试加密包含特殊字符的密码"""
        manager = SecureCommManager()
        plaintext = "p@ssw0rd!#$%^&*()"

        ciphertext = manager.encrypt_credentials(plaintext)

        assert ciphertext is not None

    def test_same_plaintext_different_ciphertext(self):
        """测试相同明文每次加密产生不同密文"""
        manager = SecureCommManager()
        plaintext = "password123"

        ciphertext1 = manager.encrypt_credentials(plaintext)
        ciphertext2 = manager.encrypt_credentials(plaintext)

        assert ciphertext1 != ciphertext2  # 不同的 nonce


class TestCredentialsDecryption:
    """测试账号密码解密"""

    def test_decrypt_credentials_success(self):
        """测试成功解密账号密码"""
        manager = SecureCommManager()
        plaintext = "password123"

        ciphertext = manager.encrypt_credentials(plaintext)
        decrypted = manager.decrypt_credentials(ciphertext)

        assert decrypted == plaintext

    def test_decrypt_with_wrong_key(self):
        """测试使用错误密钥解密"""
        manager1 = SecureCommManager()
        manager2 = SecureCommManager()  # 不同的密钥

        plaintext = "password123"
        ciphertext = manager1.encrypt_credentials(plaintext)

        with pytest.raises(ValueError, match="解密失败"):
            manager2.decrypt_credentials(ciphertext)

    def test_decrypt_tampered_ciphertext(self):
        """测试解密被篡改的密文"""
        manager = SecureCommManager()
        plaintext = "password123"

        ciphertext = manager.encrypt_credentials(plaintext)
        # 篡改密文
        tampered = ciphertext[:-1] + b'\x00'

        with pytest.raises(ValueError, match="解密失败"):
            manager.decrypt_credentials(tampered)

    def test_decrypt_invalid_ciphertext(self):
        """测试解密无效密文（长度不足）"""
        manager = SecureCommManager()

        with pytest.raises(ValueError, match="密文长度不足"):
            manager.decrypt_credentials(b"short")


class TestConfigEncryption:
    """测试配置文件加密"""

    def test_encrypt_config_success(self):
        """测试成功加密配置文件"""
        manager = SecureCommManager()
        plaintext = "config content"

        ciphertext = manager.encrypt_config(plaintext)

        assert ciphertext is not None
        assert isinstance(ciphertext, bytes)

    def test_encrypt_large_config(self):
        """测试加密大型配置文件"""
        manager = SecureCommManager()
        plaintext = "x" * (1024 * 1024)  # 1MB

        ciphertext = manager.encrypt_config(plaintext)

        assert ciphertext is not None

    def test_encrypt_json_config(self):
        """测试加密 JSON 格式配置"""
        manager = SecureCommManager()
        config = {"key": "value", "nested": {"a": 1}}
        plaintext = json.dumps(config)

        ciphertext = manager.encrypt_config(plaintext)

        assert ciphertext is not None

    def test_encrypt_config_bytes(self):
        """测试加密 bytes 类型配置"""
        manager = SecureCommManager()
        plaintext = b"binary config data"

        ciphertext = manager.encrypt_config(plaintext)

        assert ciphertext is not None


class TestConfigDecryption:
    """测试配置文件解密"""

    def test_decrypt_config_success(self):
        """测试成功解密配置文件"""
        manager = SecureCommManager()
        plaintext = "config content"

        ciphertext = manager.encrypt_config(plaintext)
        decrypted = manager.decrypt_config(ciphertext)

        assert decrypted.decode('utf-8') == plaintext

    def test_decrypt_large_config(self):
        """测试解密大型配置文件"""
        manager = SecureCommManager()
        plaintext = "x" * (1024 * 1024)  # 1MB

        ciphertext = manager.encrypt_config(plaintext)
        decrypted = manager.decrypt_config(ciphertext)

        assert decrypted.decode('utf-8') == plaintext

    def test_decrypt_config_failure(self):
        """测试解密失败处理"""
        manager1 = SecureCommManager()
        manager2 = SecureCommManager()

        plaintext = "config content"
        ciphertext = manager1.encrypt_config(plaintext)

        with pytest.raises(ValueError, match="解密失败"):
            manager2.decrypt_config(ciphertext)


class TestEncryptDecryptRoundtrip:
    """测试加解密往返"""

    def test_credentials_roundtrip(self):
        """测试账号密码加解密往返"""
        manager = SecureCommManager()
        original = "my_password_123"

        encrypted = manager.encrypt_credentials(original)
        decrypted = manager.decrypt_credentials(encrypted)

        assert decrypted == original

    def test_config_roundtrip(self):
        """测试配置文件加解密往返"""
        manager = SecureCommManager()
        original = "config data"

        encrypted = manager.encrypt_config(original)
        decrypted = manager.decrypt_config(encrypted)

        assert decrypted.decode('utf-8') == original

    def test_shared_key_roundtrip(self):
        """测试使用共享密钥的加解密往返"""
        key = b"a" * 32  # 256 位密钥
        manager1 = SecureCommManager(key=key)
        manager2 = SecureCommManager(key=key)

        original = "shared secret"
        encrypted = manager1.encrypt_credentials(original)
        decrypted = manager2.decrypt_credentials(encrypted)

        assert decrypted == original


class TestKeyManagement:
    """测试密钥管理"""

    def test_auto_generate_key(self):
        """测试自动生成密钥"""
        manager = SecureCommManager()
        plaintext = "test"

        # 应该能正常加解密
        encrypted = manager.encrypt_credentials(plaintext)
        decrypted = manager.decrypt_credentials(encrypted)

        assert decrypted == plaintext

    def test_custom_key(self):
        """测试自定义密钥"""
        key = b"b" * 32
        manager = SecureCommManager(key=key)
        plaintext = "test"

        encrypted = manager.encrypt_credentials(plaintext)
        decrypted = manager.decrypt_credentials(encrypted)

        assert decrypted == plaintext

    def test_invalid_key_length(self):
        """测试无效密钥长度"""
        with pytest.raises(ValueError, match="密钥长度必须为 32 字节"):
            SecureCommManager(key=b"short")
