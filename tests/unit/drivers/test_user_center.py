"""UserCenter 单元测试

测试 UserCenter 模块的所有功能：
- 账号生命周期管理
- 凭据校验
- 资源登记与查询
- ACL 授权管理
- 私有检测配置内容管理
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from sdpj.drivers.user_center import UserCenter


@pytest.fixture
def mock_user_db():
    return AsyncMock()


@pytest.fixture
def user_center(mock_user_db):
    return UserCenter(mock_user_db)


# ==================== 账号生命周期测试 ====================

@pytest.mark.asyncio
async def test_register_user_success(user_center, mock_user_db):
    username = "testuser"
    password = "password123"
    mock_user_db.create_user.return_value = 1
    user_id = await user_center.register_user(username, password)
    assert user_id == 1
    mock_user_db.create_user.assert_called_once_with(username, password)


@pytest.mark.asyncio
async def test_register_user_duplicate_username(user_center, mock_user_db):
    """测试注册重复账号"""
    # 配置 mock：模拟账号已存在
    mock_user_db.create_user.side_effect = ValueError("账号已存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="账号已存在"):
        await user_center.register_user("duplicate", "password")


@pytest.mark.asyncio
async def test_delete_user_success(user_center, mock_user_db):
    """测试成功注销用户"""
    # 配置 mock
    mock_user_db.delete_user.return_value = True

    # 执行测试
    result = await user_center.delete_user(1)

    # 验证结果
    assert result is True
    mock_user_db.delete_user.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_update_user_password_success(user_center, mock_user_db):
    mock_user_db.update_user_password.return_value = True
    result = await user_center.update_user_password(1, "newpassword456")
    assert result is True
    mock_user_db.update_user_password.assert_called_once_with(1, "newpassword456")


@pytest.mark.asyncio
async def test_update_user_password_user_not_found(user_center, mock_user_db):
    """测试修改不存在用户的密码"""
    # 配置 mock：模拟用户不存在
    mock_user_db.update_user_password.side_effect = ValueError("用户不存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="用户不存在"):
        await user_center.update_user_password(999, "newpassword")


@pytest.mark.asyncio
async def test_get_user_by_username_success(user_center, mock_user_db):
    """测试按账号查询用户成功"""
    # 准备测试数据
    username = "testuser"
    mock_user_data = {
        "user_id": 1,
        "username": username,
        "password": "password123",
        "created_at": datetime(2026, 5, 1, 10, 0, 0)
    }

    # 配置 mock
    mock_user_db.get_user_by_username.return_value = mock_user_data

    # 执行测试
    result = await user_center.get_user_by_username(username)

    # 验证结果：不应包含 password_hash
    assert result is not None
    assert result["user_id"] == 1
    assert result["username"] == username
    assert result["created_at"] == datetime(2026, 5, 1, 10, 0, 0)
    assert "password_hash" not in result
    mock_user_db.get_user_by_username.assert_called_once_with(username)


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(user_center, mock_user_db):
    """测试按账号查询用户不存在"""
    # 配置 mock
    mock_user_db.get_user_by_username.return_value = None

    # 执行测试
    result = await user_center.get_user_by_username("nonexistent")

    # 验证结果
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_center, mock_user_db):
    """测试按 ID 查询用户成功"""
    # 准备测试数据
    user_id = 1
    mock_user_data = {
        "user_id": user_id,
        "username": "testuser",
        "password": "password123",
        "created_at": datetime(2026, 5, 1, 10, 0, 0)
    }

    # 配置 mock
    mock_user_db.get_user_by_id.return_value = mock_user_data

    # 执行测试
    result = await user_center.get_user_by_id(user_id)

    # 验证结果：不应包含 password_hash
    assert result is not None
    assert result["user_id"] == user_id
    assert result["username"] == "testuser"
    assert result["created_at"] == datetime(2026, 5, 1, 10, 0, 0)
    assert "password_hash" not in result
    mock_user_db.get_user_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_center, mock_user_db):
    """测试按 ID 查询用户不存在"""
    # 配置 mock
    mock_user_db.get_user_by_id.return_value = None

    # 执行测试
    result = await user_center.get_user_by_id(999)

    # 验证结果
    assert result is None


# ==================== 凭据校验测试 ====================

@pytest.mark.asyncio
async def test_verify_credentials_success(user_center, mock_user_db):
    username = "testuser"
    password = "password123"
    mock_user_db.get_user_by_username.return_value = {
        "user_id": 1, "username": username, "password": password,
        "created_at": datetime(2026, 5, 1, 10, 0, 0)
    }
    success, user_id, error_msg = await user_center.verify_credentials(username, password)
    assert success is True
    assert user_id == 1
    assert error_msg == ""


@pytest.mark.asyncio
async def test_verify_credentials_wrong_password(user_center, mock_user_db):
    mock_user_db.get_user_by_username.return_value = {
        "user_id": 1, "username": "testuser", "password": "password123",
        "created_at": datetime(2026, 5, 1, 10, 0, 0)
    }
    success, user_id, error_msg = await user_center.verify_credentials("testuser", "wrongpassword")
    assert success is False
    assert user_id is None
    assert error_msg == "密码错误"


@pytest.mark.asyncio
async def test_verify_credentials_user_not_found(user_center, mock_user_db):
    """测试凭据校验失败：用户不存在"""
    mock_user_db.get_user_by_username.return_value = None

    success, user_id, error_msg = await user_center.verify_credentials("nonexistent", "password")

    assert success is False
    assert user_id is None
    assert error_msg == "账号未注册，请先注册"


# ==================== 资源登记与查询测试 ====================

@pytest.mark.asyncio
async def test_register_resource_success(user_center, mock_user_db):
    """测试成功登记资源"""
    # 准备测试数据
    resource_type = "private_config"
    owner_user_id = 1
    expected_resource_id = 10

    # 配置 mock
    mock_user_db.register_resource.return_value = expected_resource_id

    # 执行测试
    resource_id = await user_center.register_resource(resource_type, owner_user_id)

    # 验证结果
    assert resource_id == expected_resource_id
    mock_user_db.register_resource.assert_called_once_with(resource_type, owner_user_id)


@pytest.mark.asyncio
async def test_register_resource_invalid_owner(user_center, mock_user_db):
    """测试登记资源失败：拥有者不存在"""
    # 配置 mock
    mock_user_db.register_resource.side_effect = ValueError("拥有者用户不存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="拥有者用户不存在"):
        await user_center.register_resource("private_config", 999)


@pytest.mark.asyncio
async def test_delete_resource_success(user_center, mock_user_db):
    """测试成功删除资源"""
    # 配置 mock
    mock_user_db.delete_resource.return_value = True

    # 执行测试
    result = await user_center.delete_resource(10)

    # 验证结果
    assert result is True
    mock_user_db.delete_resource.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_get_resources_by_owner_success(user_center, mock_user_db):
    """测试按拥有者查询资源清单"""
    # 准备测试数据
    user_id = 1
    mock_resources = [
        {
            "resource_id": 10,
            "resource_type": "private_config",
            "owner_user_id": user_id,
            "created_at": datetime(2026, 5, 1, 10, 0, 0)
        },
        {
            "resource_id": 11,
            "resource_type": "private_dataset",
            "owner_user_id": user_id,
            "created_at": datetime(2026, 5, 2, 11, 0, 0)
        }
    ]

    # 配置 mock
    mock_user_db.get_resources_by_owner.return_value = mock_resources

    # 执行测试
    result = await user_center.get_resources_by_owner(user_id)

    # 验证结果
    assert len(result) == 2
    assert result[0]["resource_id"] == 10
    assert result[1]["resource_id"] == 11
    mock_user_db.get_resources_by_owner.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_resource_by_id_success(user_center, mock_user_db):
    """测试按 ID 查询资源成功"""
    # 准备测试数据
    resource_id = 10
    mock_resource = {
        "resource_id": resource_id,
        "resource_type": "private_config",
        "owner_user_id": 1,
        "created_at": datetime(2026, 5, 1, 10, 0, 0)
    }

    # 配置 mock
    mock_user_db.get_resource_by_id.return_value = mock_resource

    # 执行测试
    result = await user_center.get_resource_by_id(resource_id)

    # 验证结果
    assert result is not None
    assert result["resource_id"] == resource_id
    assert result["resource_type"] == "private_config"
    mock_user_db.get_resource_by_id.assert_called_once_with(resource_id)


@pytest.mark.asyncio
async def test_get_resource_by_id_not_found(user_center, mock_user_db):
    """测试按 ID 查询资源不存在"""
    # 配置 mock
    mock_user_db.get_resource_by_id.return_value = None

    # 执行测试
    result = await user_center.get_resource_by_id(999)

    # 验证结果
    assert result is None


# ==================== ACL 授权管理测试 ====================

@pytest.mark.asyncio
async def test_grant_access_success(user_center, mock_user_db):
    """测试成功授予访问权"""
    # 准备测试数据
    resource_id = 10
    grantee_user_id = 2
    expected_acl_id = 100

    # 配置 mock
    mock_user_db.add_access_control.return_value = expected_acl_id

    # 执行测试
    acl_id = await user_center.grant_access(resource_id, grantee_user_id)

    # 验证结果
    assert acl_id == expected_acl_id
    mock_user_db.add_access_control.assert_called_once_with(resource_id, grantee_user_id)


@pytest.mark.asyncio
async def test_grant_access_invalid_resource(user_center, mock_user_db):
    """测试授予访问权失败：资源不存在"""
    # 配置 mock
    mock_user_db.add_access_control.side_effect = ValueError("资源不存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="资源不存在"):
        await user_center.grant_access(999, 2)


@pytest.mark.asyncio
async def test_revoke_access_success(user_center, mock_user_db):
    """测试成功移除访问权"""
    # 配置 mock
    mock_user_db.delete_access_control.return_value = True

    # 执行测试
    result = await user_center.revoke_access(100)

    # 验证结果
    assert result is True
    mock_user_db.delete_access_control.assert_called_once_with(100)


@pytest.mark.asyncio
async def test_get_access_list_success(user_center, mock_user_db):
    """测试查询资源授权清单"""
    # 准备测试数据
    resource_id = 10
    mock_acl_list = [
        {
            "acl_id": 100,
            "resource_id": resource_id,
            "grantee_user_id": 2,
            "created_at": datetime(2026, 5, 1, 10, 0, 0)
        },
        {
            "acl_id": 101,
            "resource_id": resource_id,
            "grantee_user_id": 3,
            "created_at": datetime(2026, 5, 2, 11, 0, 0)
        }
    ]

    # 配置 mock
    mock_user_db.get_access_controls_by_resource.return_value = mock_acl_list

    # 执行测试
    result = await user_center.get_access_list(resource_id)

    # 验证结果
    assert len(result) == 2
    assert result[0]["acl_id"] == 100
    assert result[1]["acl_id"] == 101
    mock_user_db.get_access_controls_by_resource.assert_called_once_with(resource_id)


@pytest.mark.asyncio
async def test_check_access_has_permission(user_center, mock_user_db):
    """测试判定用户具备访问权"""
    # 配置 mock
    mock_user_db.check_access_control_exists.return_value = True

    # 执行测试
    result = await user_center.check_access(10, 2)

    # 验证结果
    assert result is True
    mock_user_db.check_access_control_exists.assert_called_once_with(10, 2)


@pytest.mark.asyncio
async def test_check_access_no_permission(user_center, mock_user_db):
    """测试判定用户不具备访问权"""
    # 配置 mock
    mock_user_db.check_access_control_exists.return_value = False

    # 执行测试
    result = await user_center.check_access(10, 3)

    # 验证结果
    assert result is False


# ==================== 私有检测配置内容管理测试 ====================

@pytest.mark.asyncio
async def test_write_private_config_success(user_center, mock_user_db):
    """测试成功写入私有配置"""
    # 准备测试数据
    config_id = 10
    config_content = {"key": "value", "setting": 123}

    # 配置 mock
    mock_user_db.write_private_config.return_value = True

    # 执行测试
    result = await user_center.write_private_config(config_id, config_content)

    # 验证结果
    assert result is True
    mock_user_db.write_private_config.assert_called_once_with(config_id, config_content)


@pytest.mark.asyncio
async def test_write_private_config_resource_not_found(user_center, mock_user_db):
    """测试写入私有配置失败：资源不存在"""
    # 配置 mock
    mock_user_db.write_private_config.side_effect = ValueError("资源不存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="资源不存在"):
        await user_center.write_private_config(999, {"key": "value"})


@pytest.mark.asyncio
async def test_write_private_config_already_exists(user_center, mock_user_db):
    """测试写入私有配置失败：配置已存在"""
    # 配置 mock
    mock_user_db.write_private_config.side_effect = ValueError("配置已存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="配置已存在"):
        await user_center.write_private_config(10, {"key": "value"})


@pytest.mark.asyncio
async def test_read_private_config_success(user_center, mock_user_db):
    """测试成功读取私有配置"""
    # 准备测试数据
    config_id = 10
    mock_config = {"key": "value", "setting": 123}

    # 配置 mock
    mock_user_db.read_private_config.return_value = mock_config

    # 执行测试
    result = await user_center.read_private_config(config_id)

    # 验证结果
    assert result == mock_config
    mock_user_db.read_private_config.assert_called_once_with(config_id)


@pytest.mark.asyncio
async def test_read_private_config_not_found(user_center, mock_user_db):
    """测试读取私有配置不存在"""
    # 配置 mock
    mock_user_db.read_private_config.return_value = None

    # 执行测试
    result = await user_center.read_private_config(999)

    # 验证结果
    assert result is None


@pytest.mark.asyncio
async def test_update_private_config_success(user_center, mock_user_db):
    """测试成功更新私有配置"""
    # 准备测试数据
    config_id = 10
    new_config_content = {"key": "new_value", "setting": 456}

    # 配置 mock
    mock_user_db.update_private_config.return_value = True

    # 执行测试
    result = await user_center.update_private_config(config_id, new_config_content)

    # 验证结果
    assert result is True
    mock_user_db.update_private_config.assert_called_once_with(config_id, new_config_content)


@pytest.mark.asyncio
async def test_update_private_config_not_found(user_center, mock_user_db):
    """测试更新私有配置失败：配置不存在"""
    # 配置 mock
    mock_user_db.update_private_config.side_effect = ValueError("配置不存在")

    # 执行测试并验证异常
    with pytest.raises(ValueError, match="配置不存在"):
        await user_center.update_private_config(999, {"key": "value"})


@pytest.mark.asyncio
async def test_delete_private_config_success(user_center, mock_user_db):
    """测试成功删除私有配置"""
    # 配置 mock
    mock_user_db.delete_private_config.return_value = True

    # 执行测试
    result = await user_center.delete_private_config(10)

    # 验证结果
    assert result is True
    mock_user_db.delete_private_config.assert_called_once_with(10)

