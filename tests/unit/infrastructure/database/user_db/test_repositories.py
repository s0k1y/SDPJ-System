"""UserDB 仓储层测试"""

import pytest

from sdpj.infrastructure.database.user_db import UserDB


@pytest.mark.asyncio
class TestUserRepository:
    """测试用户仓储"""

    async def test_create_user(self, user_db):
        """测试创建用户"""
        user_id = await user_db.create_user("newuser", "hashed_password")
        assert user_id > 0

    async def test_create_duplicate_user(self, user_db, sample_user):
        """测试创建重复用户"""
        with pytest.raises(ValueError, match="已存在"):
            await user_db.create_user(sample_user["username"], "another_password")

    async def test_get_user_by_username(self, user_db, sample_user):
        """测试按账号查询用户"""
        user = await user_db.get_user_by_username(sample_user["username"])
        assert user is not None
        assert user["user_id"] == sample_user["user_id"]
        assert user["username"] == sample_user["username"]

    async def test_get_user_by_id(self, user_db, sample_user):
        """测试按 ID 查询用户"""
        user = await user_db.get_user_by_id(sample_user["user_id"])
        assert user is not None
        assert user["user_id"] == sample_user["user_id"]
        assert user["username"] == sample_user["username"]

    async def test_get_nonexistent_user(self, user_db):
        """测试查询不存在的用户"""
        user = await user_db.get_user_by_username("nonexistent")
        assert user is None

        user = await user_db.get_user_by_id(99999)
        assert user is None

    async def test_update_user_password(self, user_db, sample_user):
        """测试更新用户密码"""
        result = await user_db.update_user_password(sample_user["user_id"], "new_hashed_password")
        assert result is True

        # 验证密码已更新
        user = await user_db.get_user_by_id(sample_user["user_id"])
        assert user["password_hash"] == "new_hashed_password"

    async def test_update_nonexistent_user_password(self, user_db):
        """测试更新不存在用户的密码"""
        with pytest.raises(ValueError, match="不存在"):
            await user_db.update_user_password(99999, "new_password")

    async def test_delete_user(self, user_db, sample_user):
        """测试删除用户"""
        result = await user_db.delete_user(sample_user["user_id"])
        assert result is True

        # 验证用户已删除
        user = await user_db.get_user_by_id(sample_user["user_id"])
        assert user is None



@pytest.mark.asyncio
class TestResourceRepository:
    """测试资源仓储"""

    async def test_register_resource(self, user_db, sample_user):
        """测试登记资源"""
        resource_id = await user_db.register_resource("private_config", sample_user["user_id"])
        assert resource_id > 0

    async def test_register_resource_with_invalid_owner(self, user_db):
        """测试使用无效拥有者登记资源"""
        with pytest.raises(ValueError, match="不存在"):
            await user_db.register_resource("private_config", 99999)

    async def test_get_resource_by_id(self, user_db, sample_resource):
        """测试按 ID 查询资源"""
        resource = await user_db.get_resource_by_id(sample_resource["resource_id"])
        assert resource is not None
        assert resource["resource_id"] == sample_resource["resource_id"]
        assert resource["resource_type"] == sample_resource["resource_type"]
        assert resource["owner_user_id"] == sample_resource["owner_user_id"]

    async def test_get_resources_by_owner(self, user_db, sample_user, sample_resource):
        """测试按拥有者查询资源列表"""
        resources = await user_db.get_resources_by_owner(sample_user["user_id"])
        assert len(resources) >= 1
        assert any(r["resource_id"] == sample_resource["resource_id"] for r in resources)

    async def test_delete_resource(self, user_db, sample_resource):
        """测试删除资源"""
        result = await user_db.delete_resource(sample_resource["resource_id"])
        assert result is True

        # 验证资源已删除
        resource = await user_db.get_resource_by_id(sample_resource["resource_id"])
        assert resource is None


@pytest.mark.asyncio
class TestACLRepository:
    """测试访问控制列表仓储"""

    async def test_add_access_control(self, user_db, sample_resource):
        """测试添加访问控制项"""
        # 创建另一个用户作为被授权者
        grantee_id = await user_db.create_user("grantee", "password")
        acl_id = await user_db.add_access_control(sample_resource["resource_id"], grantee_id)
        assert acl_id > 0

    async def test_add_duplicate_access_control(self, user_db, sample_resource):
        """测试添加重复的访问控制项（幂等）"""
        grantee_id = await user_db.create_user("grantee2", "password")
        acl_id1 = await user_db.add_access_control(sample_resource["resource_id"], grantee_id)
        acl_id2 = await user_db.add_access_control(sample_resource["resource_id"], grantee_id)
        assert acl_id1 == acl_id2

    async def test_add_access_control_with_invalid_resource(self, user_db, sample_user):
        """测试使用无效资源添加访问控制项"""
        with pytest.raises(ValueError, match="不存在"):
            await user_db.add_access_control(99999, sample_user["user_id"])

    async def test_check_access_control_exists(self, user_db, sample_resource):
        """测试判定访问控制项是否存在"""
        grantee_id = await user_db.create_user("grantee3", "password")
        await user_db.add_access_control(sample_resource["resource_id"], grantee_id)

        exists = await user_db.check_access_control_exists(sample_resource["resource_id"], grantee_id)
        assert exists is True

        not_exists = await user_db.check_access_control_exists(sample_resource["resource_id"], 99999)
        assert not_exists is False

    async def test_get_access_controls_by_resource(self, user_db, sample_resource):
        """测试按资源 ID 查询访问控制项列表"""
        grantee_id = await user_db.create_user("grantee4", "password")
        await user_db.add_access_control(sample_resource["resource_id"], grantee_id)

        acls = await user_db.get_access_controls_by_resource(sample_resource["resource_id"])
        assert len(acls) >= 1
        assert any(acl["grantee_user_id"] == grantee_id for acl in acls)

    async def test_delete_access_control(self, user_db, sample_resource):
        """测试删除访问控制项"""
        grantee_id = await user_db.create_user("grantee5", "password")
        acl_id = await user_db.add_access_control(sample_resource["resource_id"], grantee_id)

        result = await user_db.delete_access_control(acl_id)
        assert result is True

        # 验证访问控制项已删除
        exists = await user_db.check_access_control_exists(sample_resource["resource_id"], grantee_id)
        assert exists is False



@pytest.mark.asyncio
class TestPrivateConfigRepository:
    """测试私有检测配置仓储"""

    async def test_write_private_config(self, user_db, sample_resource):
        """测试写入私有检测配置内容"""
        config_content = {"detection_mode": "static", "threshold": 0.8}
        result = await user_db.write_private_config(sample_resource["resource_id"], config_content)
        assert result is True

    async def test_write_duplicate_private_config(self, user_db, sample_resource):
        """测试写入重复的私有检测配置内容"""
        config_content = {"detection_mode": "static"}
        await user_db.write_private_config(sample_resource["resource_id"], config_content)

        with pytest.raises(ValueError, match="已存在"):
            await user_db.write_private_config(sample_resource["resource_id"], config_content)

    async def test_read_private_config(self, user_db, sample_resource):
        """测试读取私有检测配置内容"""
        config_content = {"detection_mode": "dynamic", "max_retries": 3}
        await user_db.write_private_config(sample_resource["resource_id"], config_content)

        read_config = await user_db.read_private_config(sample_resource["resource_id"])
        assert read_config == config_content

    async def test_read_nonexistent_private_config(self, user_db):
        """测试读取不存在的私有检测配置内容"""
        config = await user_db.read_private_config(99999)
        assert config is None

    async def test_update_private_config(self, user_db, sample_resource):
        """测试更新私有检测配置内容"""
        original_config = {"detection_mode": "static"}
        await user_db.write_private_config(sample_resource["resource_id"], original_config)

        updated_config = {"detection_mode": "dynamic", "new_field": "value"}
        result = await user_db.update_private_config(sample_resource["resource_id"], updated_config)
        assert result is True

        # 验证配置已更新
        read_config = await user_db.read_private_config(sample_resource["resource_id"])
        assert read_config == updated_config

    async def test_update_nonexistent_private_config(self, user_db):
        """测试更新不存在的私有检测配置内容"""
        with pytest.raises(ValueError, match="不存在"):
            await user_db.update_private_config(99999, {"key": "value"})

    async def test_delete_private_config(self, user_db, sample_resource):
        """测试删除私有检测配置内容"""
        config_content = {"detection_mode": "static"}
        await user_db.write_private_config(sample_resource["resource_id"], config_content)

        result = await user_db.delete_private_config(sample_resource["resource_id"])
        assert result is True

        # 验证配置已删除
        config = await user_db.read_private_config(sample_resource["resource_id"])
        assert config is None


@pytest.mark.asyncio
class TestCascadeDelete:
    """测试级联删除"""

    async def test_delete_user_cascades_resources(self, user_db, sample_user):
        """测试删除用户时级联删除资源"""
        # 创建资源
        resource_id = await user_db.register_resource("private_config", sample_user["user_id"])

        # 删除用户
        await user_db.delete_user(sample_user["user_id"])

        # 验证资源已被级联删除
        resource = await user_db.get_resource_by_id(resource_id)
        assert resource is None

    async def test_delete_resource_cascades_acl(self, user_db, sample_user, sample_resource):
        """测试删除资源时级联删除访问控制项"""
        # 创建被授权用户和访问控制项
        grantee_id = await user_db.create_user("grantee_cascade", "password")
        await user_db.add_access_control(sample_resource["resource_id"], grantee_id)

        # 删除资源
        await user_db.delete_resource(sample_resource["resource_id"])

        # 验证访问控制项已被级联删除
        exists = await user_db.check_access_control_exists(sample_resource["resource_id"], grantee_id)
        assert exists is False

    async def test_delete_resource_cascades_private_config(self, user_db, sample_resource):
        """测试删除资源时级联删除私有配置"""
        # 创建私有配置
        config_content = {"detection_mode": "static"}
        await user_db.write_private_config(sample_resource["resource_id"], config_content)

        # 删除资源
        await user_db.delete_resource(sample_resource["resource_id"])

        # 验证私有配置已被级联删除
        config = await user_db.read_private_config(sample_resource["resource_id"])
        assert config is None
