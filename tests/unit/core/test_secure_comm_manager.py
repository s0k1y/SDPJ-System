"""
SecureCommManager 单元测试
"""
from sdpj.core.secure_comm_manager import SecureCommManager


class TestSecureCommManager:
    """测试 SecureCommManager 基本实例化"""

    def test_instantiate_default(self):
        manager = SecureCommManager()
        assert manager is not None

    def test_instantiate_with_key_path(self):
        manager = SecureCommManager(key_path="/tmp/fake.pem")
        assert manager is not None
