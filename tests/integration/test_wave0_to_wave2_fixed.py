"""Wave 0-2 集成测试（修复版）"""
import pytest


class TestWave0Integration:
    """Wave 0 基础设施层集成测试"""

    def test_task_queue_manager_import(self):
        from sdpj.core.task_queue_manager import TaskQueueManager
        manager = TaskQueueManager()
        assert manager is not None

    def test_event_logger_import(self):
        from sdpj.core.event_logger import EventLogger
        logger = EventLogger()
        assert logger is not None

    def test_secure_comm_manager_import(self):
        from sdpj.core.secure_comm_manager import SecureCommManager
        manager = SecureCommManager()
        assert manager is not None

    def test_utils_lib_import(self):
        from sdpj.infrastructure.utils.utils_lib import UtilsLib
        utils = UtilsLib()
        assert utils is not None


class TestWave1Integration:
    """Wave 1 数据库层 + 抽象驱动层集成测试"""

    def test_sample_db_import(self):
        from sdpj.infrastructure.database.sample_db import SampleDB, get_session_manager
        session_mgr = get_session_manager()
        db = SampleDB(session_mgr)
        assert db is not None

    def test_result_db_import(self):
        from sdpj.infrastructure.database.result_db import ResultDB, SessionManager
        session_mgr = SessionManager("sqlite+aiosqlite:///./test.db", echo=False)
        db = ResultDB(session_mgr)
        assert db is not None

    def test_user_db_import(self):
        from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager
        session_mgr = UserDBSessionManager("sqlite+aiosqlite:///./test.db", echo=False)
        db = UserDB(session_mgr)
        assert db is not None

    def test_llm_interface_import(self):
        from sdpj.drivers.llm_interface import LLMInterface
        interface = LLMInterface()
        assert interface is not None

    def test_llm_registry_import(self):
        from sdpj.drivers.llm_registry import LLMRegistry
        registry = LLMRegistry()
        assert registry is not None


class TestWave2Integration:
    """Wave 2 执行逻辑层集成测试"""

    def test_account_manager_import(self):
        from sdpj.core.account_manager import AccountManager
        manager = AccountManager()
        assert manager is not None

    def test_dac_manager_import(self):
        from sdpj.core.dac_manager import DACManager
        manager = DACManager()
        assert manager is not None

    def test_report_manager_import(self):
        from sdpj.core.report_manager import ReportManager
        manager = ReportManager()
        assert manager is not None

    def test_sdpj_detector_import(self):
        from sdpj.core.sdpj_detector import SDPJDetector
        detector = SDPJDetector()
        assert detector is not None


class TestCrossCutting:
    """横切关注点测试"""

    def test_encryption_roundtrip(self):
        from sdpj.core.secure_comm_manager import SecureCommManager
        manager = SecureCommManager()
        plaintext = "test_password"
        ciphertext = manager.encrypt_credentials(plaintext)
        decrypted = manager.decrypt_credentials(ciphertext)
        assert decrypted == plaintext

    def test_utils_encoding(self):
        from sdpj.infrastructure.utils.utils_lib import UtilsLib
        utils = UtilsLib()
        text = "Hello World"
        encoded = utils.base64_encode(text)
        decoded = utils.base64_decode(encoded)
        assert decoded == text
