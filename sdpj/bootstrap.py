"""组合根 — 唯一允许跨层实例化的模块"""
from functools import lru_cache
from sdpj.control.state_scheduler_interface import StateSchedulerInterface


@lru_cache(maxsize=1)
def build_scheduler() -> StateSchedulerInterface:
    from sdpj.infrastructure.utils.utils_lib import UtilsLib
    from sdpj.infrastructure.llm_adapters.llm_adapter_lib import LLMAdapterLib
    from sdpj.infrastructure.database.sample_db import SampleDB, SampleDBSessionManager
    from sdpj.infrastructure.database.result_db import ResultDB, SessionManager as ResultDBSessionManager
    from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager
    from sdpj.drivers.data_processor import DataProcessor
    from sdpj.drivers.user_center import UserCenter
    from sdpj.drivers.llm_service import LLMService
    from sdpj.drivers.llm_registry import LLMRegistry
    from sdpj.core.account_manager import AccountManager
    from sdpj.core.dac_manager import DACManager
    from sdpj.core.private_config_manager import PrivateConfigManager
    from sdpj.core.report_manager import ReportManager
    from sdpj.core.sdpj_detector import SDPJDetector
    from sdpj.core.event_logger import EventLogger
    from sdpj.core.task_queue_manager import TaskQueueManager
    from sdpj.core.secure_comm_manager import SecureCommManager
    from sdpj.control.state_scheduler import StateScheduler

    from sdpj.infrastructure.config.settings import get_settings
    cfg = get_settings()

    utils = UtilsLib()
    adapter_lib = LLMAdapterLib()
    sample_db = SampleDB(SampleDBSessionManager(cfg.sample_db_url))
    result_db = ResultDB(ResultDBSessionManager(cfg.result_db_url))
    user_db = UserDB(UserDBSessionManager(cfg.user_db_url))
    uc = UserCenter(user_db)
    dp = DataProcessor(sample_db, result_db, utils)
    llm = LLMService(adapter_lib, utils)
    reg = LLMRegistry(adapter_lib, utils)

    return StateScheduler(
        account_manager=AccountManager(uc),
        dac_manager=DACManager(uc),
        config_manager=PrivateConfigManager(dp, uc, reg),
        report_manager=ReportManager(dp, uc),
        detector=SDPJDetector(dp, llm),
        event_logger=EventLogger(),
        task_queue_manager=TaskQueueManager(),
        secure_comm_manager=SecureCommManager(),
        llm_registry=reg,
    )
