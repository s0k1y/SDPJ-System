"""Wave 0-2 集成测试"""
import pytest
import asyncio


class TestWave0Integration:
    """Wave 0 基础设施层集成测试"""

    def test_task_queue_manager_import(self):
        """测试 TaskQueueManager 导入"""
        from sdpj.core.task_queue_manager import TaskQueueManager
        manager = TaskQueueManager()
        assert manager is not None

    def test_event_logger_import(self):
        """测试 EventLogger 导入"""
        from sdpj.core.event_logger import EventLogger
        logger = EventLogger()
        assert logger is not None

    def test_secure_comm_manager_import(self):
        """测试 SecureCommManager 导入"""
        from sdpj.core.secure_comm_manager import SecureCommManager
        manager = SecureCommManager()
        assert manager is not None

    def test_utils_lib_import(self):
        """测试 UtilsLib 导入"""
        from sdpj.infrastructure.utils.utils_lib import UtilsLib
        utils = UtilsLib()
        assert utils is not None

    def test_llm_adapter_lib_import(self):
        """测试 LLMAdapterLib 导入"""
        from sdpj.infrastructure.llm_adapters.llm_adapter_lib import LLMAdapterLib
        lib = LLMAdapterLib()
        assert lib is not None


class TestWave1Integration:
    """Wave 1 数据库层 + 抽象驱动层集成测试"""

    def test_sample_db_import(self):
        """测试 SampleDB 导入"""
        from sdpj.infrastructure.database.sample_db.sample_db import SampleDB
        from sdpj.infrastructure.database.sample_db.session import SampleDBSessionManager
        session_manager = SampleDBSessionManager()
        db = SampleDB(session_manager)
        assert db is not None

    def test_result_db_import(self):
        """测试 ResultDB 导入"""
        from sdpj.infrastructure.database.result_db.result_db import ResultDB
        from sdpj.infrastructure.database.result_db.session import SessionManager
        session_manager = SessionManager("sqlite+aiosqlite:///:memory:")
        db = ResultDB(session_manager)
        assert db is not None

    def test_user_db_import(self):
        """测试 UserDB 导入"""
        from sdpj.infrastructure.database.user_db.user_db import UserDB
        from sdpj.infrastructure.database.user_db.session import UserDBSessionManager
        session_manager = UserDBSessionManager("sqlite+aiosqlite:///:memory:")
        db = UserDB(session_manager)
        assert db is not None

    def test_data_processor_import(self):
        """测试 DataProcessor 导入"""
        from sdpj.drivers.data_processor import DataProcessor
        processor = DataProcessor()
        assert processor is not None

    def test_llm_interface_import(self):
        """测试 LLMInterface 导入"""
        from sdpj.drivers.llm_interface import LLMInterface
        interface = LLMInterface()
        assert interface is not None

    def test_llm_registry_import(self):
        """测试 LLMRegistry 导入"""
        from sdpj.drivers.llm_registry import LLMRegistry
        registry = LLMRegistry()
        assert registry is not None

    def test_user_center_import(self):
        """测试 UserCenter 导入"""
        from sdpj.drivers.user_center import UserCenter
        center = UserCenter()
        assert center is not None


class TestWave2Integration:
    """Wave 2 执行逻辑层集成测试"""

    def test_sdpj_detector_import(self):
        """测试 SDPJDetector 导入"""
        from sdpj.core.sdpj_detector import SDPJDetector
        detector = SDPJDetector()
        assert detector is not None

    def test_account_manager_import(self):
        """测试 AccountManager 导入"""
        from sdpj.core.account_manager import AccountManager
        manager = AccountManager()
        assert manager is not None

    def test_dac_manager_import(self):
        """测试 DACManager 导入"""
        from sdpj.core.dac_manager import DACManager
        manager = DACManager()
        assert manager is not None

    def test_private_config_manager_import(self):
        """测试 PrivateConfigManager 导入"""
        from sdpj.core.private_config_manager import PrivateConfigManager
        manager = PrivateConfigManager()
        assert manager is not None

    def test_report_manager_import(self):
        """测试 ReportManager 导入"""
        from sdpj.core.report_manager import ReportManager
        manager = ReportManager()
        assert manager is not None


class TestVerticalSlice:
    """垂直切片测试：用户注册 -> 登录 -> 创建配置"""

    @pytest.mark.asyncio
    async def test_user_registration_and_login(self):
        """测试用户注册和登录流程"""
        from sdpj.core.account_manager import AccountManager
        import uuid

        manager = AccountManager()
        await manager.init()

        # 创建表
        await manager.user_center.user_db._session_manager.create_tables()

        # 使用唯一用户名避免冲突
        unique_username = f"testuser_{uuid.uuid4().hex[:8]}"

        # 注册
        success, msg = await manager.register(unique_username, "password123")
        assert success is True

        # 登录
        success, session_id = await manager.login(unique_username, "password123")
        assert success is True
        assert session_id is not None

        # 登出
        result = manager.logout(session_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_data_processor_initialization(self):
        """测试 DataProcessor 初始化"""
        from sdpj.drivers.data_processor import DataProcessor

        processor = DataProcessor()
        await processor.init()

        # 测试序列化
        data = {"key": "value"}
        json_str = processor.serialize_data(data, "json")
        assert "key" in json_str

        # 测试反序列化
        result = processor.deserialize_data(json_str, "json")
        assert result["key"] == "value"

    @pytest.mark.asyncio
    async def test_llm_registry_startup(self):
        """测试 LLMRegistry 启动"""
        from sdpj.drivers.llm_registry import LLMRegistry

        registry = LLMRegistry()
        await registry.startup()

        # 检查内置模型
        models = registry.list_models()
        assert len(models) > 0
        assert "gpt-4" in models or "claude-3" in models

    @pytest.mark.asyncio
    async def test_report_statistics_calculation(self):
        """测试报告统计计算"""
        from sdpj.core.report_manager import ReportManager

        manager = ReportManager()

        # 测试空结果
        stats = manager.calculate_statistics([])
        assert stats["total"] == 0
        assert stats["risk_level"] == "优秀"

        # 测试有结果
        results = [
            {"compliance": "合规"},
            {"compliance": "违规"},
            {"compliance": "合规"},
        ]
        stats = manager.calculate_statistics(results)
        assert stats["total"] == 3
        assert stats["compliant"] == 2
        assert stats["non_compliant"] == 1


class TestCrossCutting:
    """横切关注点测试"""

    def test_encryption_roundtrip(self):
        """测试加密解密往返"""
        from sdpj.core.secure_comm_manager import SecureCommManager

        manager = SecureCommManager()
        plaintext = "test_password"

        # 加密
        ciphertext = manager.encrypt_credentials(plaintext)
        assert ciphertext != plaintext.encode()

        # 解密
        decrypted = manager.decrypt_credentials(ciphertext)
        assert decrypted == plaintext

    def test_utils_encoding(self):
        """测试编码工具"""
        from sdpj.infrastructure.utils.utils_lib import UtilsLib

        utils = UtilsLib()

        # Base64 编码
        text = "Hello World"
        encoded = utils.base64_encode(text)
        decoded = utils.base64_decode(encoded)
        assert decoded == text

        # URL 编码
        url_text = "hello world"
        url_encoded = utils.url_encode(url_text)
        url_decoded = utils.url_decode(url_encoded)
        assert url_decoded == url_text

    @pytest.mark.asyncio
    async def test_task_queue_fifo(self):
        """测试任务队列 FIFO"""
        from sdpj.core.task_queue_manager import TaskQueueManager

        manager = TaskQueueManager()

        # 入队 - 添加必需的 algorithm_type 字段
        task1 = {"user_id": 1, "model_id": "gpt-4", "dataset_id": 1, "algorithm_type": "static"}
        task2 = {"user_id": 2, "model_id": "claude-3", "dataset_id": 2, "algorithm_type": "dynamic"}

        id1 = await manager.enqueue_task(task1)
        id2 = await manager.enqueue_task(task2)

        # 出队验证 FIFO - Task 是 dataclass，使用属性访问
        dequeued1 = await manager.dequeue_task()
        assert dequeued1.task_id == id1

        dequeued2 = await manager.dequeue_task()
        assert dequeued2.task_id == id2
