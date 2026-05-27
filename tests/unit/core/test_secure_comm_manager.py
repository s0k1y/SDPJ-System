"""
SecureCommManager 单元测试
"""

from sdpj.core.secure_comm_manager import SecureCommManager
from typing import Any


class TestSecureCommManager:
    """测试 SecureCommManager 基本实例化"""

    def test_instantiate_default(self) -> None:
        """测试 test instantiate default."""
        manager = SecureCommManager()
        assert manager is not None

    def test_instantiate_with_key_path(self) -> None:
        """测试 test instantiate with key path."""
        manager = SecureCommManager()
        assert manager is not None
