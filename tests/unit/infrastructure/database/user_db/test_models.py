"""UserDB 模型测试"""

import pytest
from datetime import datetime

from sdpj.infrastructure.database.user_db.models import User, Resource, AccessControl, PrivateConfig


class TestUserModel:
    """测试 User 模型"""

    def test_user_creation(self):
        """测试用户对象创建"""
        user = User(username="testuser", password_hash="hashed_password")
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.user_id is None  # 未持久化前为 None

    def test_user_repr(self):
        """测试用户对象字符串表示"""
        user = User(username="testuser", password_hash="hashed_password")
        user.user_id = 1
        assert "user_id=1" in repr(user)
        assert "username='testuser'" in repr(user)


class TestResourceModel:
    """测试 Resource 模型"""

    def test_resource_creation(self):
        """测试资源对象创建"""
        resource = Resource(resource_type="private_config", owner_user_id=1)
        assert resource.resource_type == "private_config"
        assert resource.owner_user_id == 1
        assert resource.resource_id is None

    def test_resource_repr(self):
        """测试资源对象字符串表示"""
        resource = Resource(resource_type="private_config", owner_user_id=1)
        resource.resource_id = 10
        assert "resource_id=10" in repr(resource)
        assert "type='private_config'" in repr(resource)
        assert "owner_id=1" in repr(resource)


class TestAccessControlModel:
    """测试 AccessControl 模型"""

    def test_acl_creation(self):
        """测试访问控制项对象创建"""
        acl = AccessControl(resource_id=10, grantee_user_id=2)
        assert acl.resource_id == 10
        assert acl.grantee_user_id == 2
        assert acl.acl_id is None

    def test_acl_repr(self):
        """测试访问控制项对象字符串表示"""
        acl = AccessControl(resource_id=10, grantee_user_id=2)
        acl.acl_id = 100
        assert "acl_id=100" in repr(acl)
        assert "resource_id=10" in repr(acl)
        assert "grantee_id=2" in repr(acl)


class TestPrivateConfigModel:
    """测试 PrivateConfig 模型"""

    def test_private_config_creation(self):
        """测试私有配置对象创建"""
        config = PrivateConfig(config_id=10, config_content='{"key": "value"}')
        assert config.config_id == 10
        assert config.config_content == '{"key": "value"}'

    def test_private_config_repr(self):
        """测试私有配置对象字符串表示"""
        config = PrivateConfig(config_id=10, config_content='{"key": "value"}')
        assert "config_id=10" in repr(config)
