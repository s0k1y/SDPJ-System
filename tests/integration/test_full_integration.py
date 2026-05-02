"""完整集成测试 - 跨层级模块协作"""
import pytest
import asyncio


class TestWave0ToWave2Integration:
    """Wave 0-2 垂直集成测试"""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self):
        """测试用户注册完整流程（UserCenter -> UserDB -> 数据库）"""
        from sdpj.drivers.user_center import UserCenter
        import uuid

        user_center = UserCenter()
        await user_center.init()

        # 创建表
        await user_center.user_db._session_manager.create_tables()

        # 使用唯一用户名
        unique_username = f"test_user_{uuid.uuid4().hex[:8]}"

        # 注册用户
        user_id = await user_center.register_user(unique_username, "password12345")
        assert user_id > 0

        # 验证登录
        success, verified_user_id = await user_center.verify_login(unique_username, "password12345")
        assert success is True
        assert verified_user_id == user_id

    @pytest.mark.asyncio
    async def test_data_processor_initialization(self):
        """测试 DataProcessor 初始化（跨数据库）"""
        from sdpj.drivers.data_processor import DataProcessor
        
        processor = DataProcessor()
        await processor.init()
        
        # 验证数据库连接已建立
        assert processor.sample_db is not None
        assert processor.result_db is not None
        assert processor.utils is not None


class TestWave2ToWave3Integration:
    """Wave 2-3 垂直集成测试"""

    @pytest.mark.asyncio
    async def test_state_scheduler_with_account_manager(self):
        """测试 StateScheduler 调度 AccountManager"""
        from sdpj.control.state_scheduler import StateScheduler
        import uuid

        scheduler = StateScheduler()
        await scheduler.init()

        # 创建表
        await scheduler.account_manager.user_center.user_db._session_manager.create_tables()

        # 使用唯一用户名
        unique_username = f"scheduler_user_{uuid.uuid4().hex[:8]}"

        # 通过 StateScheduler 注册用户
        result = await scheduler.register_user(unique_username, "password12345")

        # 打印结果以便调试
        if not result["success"]:
            print(f"注册失败: {result}")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_state_scheduler_detection_flow(self):
        """测试 StateScheduler 检测流程"""
        from sdpj.control.state_scheduler import StateScheduler
        
        scheduler = StateScheduler()
        await scheduler.init()
        
        # 启动检测
        config_data = {
            "model_id": "gpt-4",
            "dataset_id": 1,
            "algorithm_type": "static"
        }
        
        result = await scheduler.start_detection(user_id=1, config_data=config_data)
        assert result["success"] is True
        assert "task_id" in result


class TestWave3ToWave4Integration:
    """Wave 3-4 垂直集成测试"""

    @pytest.mark.asyncio
    async def test_webui_backend_with_state_scheduler(self):
        """测试 WebUI Backend 调用 StateScheduler"""
        from fastapi.testclient import TestClient
        from sdpj.ui.webui_backend import app
        
        client = TestClient(app)
        
        # 测试系统状态
        response = client.get("/api/status")
        assert response.status_code == 200
        assert "status" in response.json()

    @pytest.mark.asyncio
    async def test_webui_backend_register_flow(self):
        """测试 WebUI Backend 注册流程"""
        from fastapi.testclient import TestClient
        from sdpj.ui.webui_backend import app
        
        client = TestClient(app)
        
        # 注册用户
        response = client.post("/api/auth/register", json={
            "username": "webui_test_user",
            "password": "password12345"
        })
        assert response.status_code in [200, 400]  # 可能已存在


class TestCrossLayerIntegration:
    """跨层级集成测试"""

    @pytest.mark.asyncio
    async def test_full_stack_detection_flow(self):
        """测试完整检测流程（Wave 0 -> Wave 1 -> Wave 2 -> Wave 3）"""
        from sdpj.control.state_scheduler import StateScheduler
        
        scheduler = StateScheduler()
        await scheduler.init()
        
        # 1. 检查系统状态
        initial_state = scheduler.get_system_state()
        assert initial_state == "idle"
        
        # 2. 启动检测任务
        config_data = {
            "model_id": "gpt-4",
            "dataset_id": 1,
            "algorithm_type": "static"
        }
        
        result = await scheduler.start_detection(user_id=1, config_data=config_data)
        assert result["success"] is True
        
        # 3. 验证任务已入队
        task_id = result["task_id"]
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_encryption_across_layers(self):
        """测试加密功能（同一实例）"""
        from sdpj.core.secure_comm_manager import SecureCommManager

        # 使用同一个实例进行加密解密
        secure_comm = SecureCommManager()
        plaintext = "test_password"
        encrypted = secure_comm.encrypt_credentials(plaintext)
        decrypted = secure_comm.decrypt_credentials(encrypted)

        assert decrypted == plaintext
