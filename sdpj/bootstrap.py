"""组合根 — 唯一允许跨层实例化的模块"""
from functools import lru_cache
from pathlib import Path

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
    from sdpj.control.state_scheduler import StateScheduler

    from sdpj.infrastructure.config.settings import get_settings
    cfg = get_settings()

    from sqlalchemy import event as _event
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool, StaticPool
    _is_memory = ":memory:" in cfg.db_url
    _engine = create_async_engine(
        cfg.db_url,
        poolclass=StaticPool if _is_memory else NullPool,
        connect_args={"check_same_thread": False},
    )
    if "sqlite" in cfg.db_url:
        @_event.listens_for(_engine.sync_engine, "connect")
        def _enable_fk(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    utils = UtilsLib()
    adapter_lib = LLMAdapterLib()
    sample_sm = SampleDBSessionManager(cfg.db_url, engine=_engine)
    result_sm = ResultDBSessionManager(cfg.db_url, engine=_engine)
    user_sm = UserDBSessionManager(cfg.db_url, engine=_engine)

    from sdpj.infrastructure.database.sample_db.builtin_datasets import load_builtin_datasets

    async def _init_db():
        await user_sm.create_tables()
        await sample_sm.create_tables()
        await result_sm.create_tables()
        await load_builtin_datasets(sample_db)

    sample_db = SampleDB(sample_sm)
    result_db = ResultDB(result_sm)
    user_db = UserDB(user_sm)
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
        event_logger=EventLogger(result_db=result_db),
        task_queue_manager=TaskQueueManager(session_manager=result_sm),
        llm_registry=reg,
        db_initializer=_init_db,
    )
