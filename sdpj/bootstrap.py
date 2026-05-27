"""组合根 — 唯一允许跨层实例化的模块."""

from functools import lru_cache
from typing import TYPE_CHECKING, cast

from sdpj.control.state_scheduler_interface import StateSchedulerInterface

if TYPE_CHECKING:
    from sdpj.drivers.llm_service_interface import LLMServiceInterface


@lru_cache(maxsize=1)
def build_scheduler(  # noqa: D103
    skip_builtin_datasets: bool = False,  # noqa: ARG001, FBT001, FBT002
    skip_adapter_restore: bool = False,  # noqa: ARG001, FBT001, FBT002
) -> StateSchedulerInterface:
    from sdpj.control.state_scheduler import StateScheduler  # noqa: PLC0415
    from sdpj.core.account_manager import AccountManager  # noqa: PLC0415
    from sdpj.core.dac_manager import DACManager  # noqa: PLC0415
    from sdpj.core.event_logger import EventLogger  # noqa: PLC0415
    from sdpj.core.private_config_manager import PrivateConfigManager  # noqa: PLC0415
    from sdpj.core.report_manager import ReportManager  # noqa: PLC0415
    from sdpj.core.sdpj_detector import SDPJDetector  # noqa: PLC0415
    from sdpj.core.task_queue_manager import TaskQueueManager  # noqa: PLC0415
    from sdpj.drivers.data_processor import DataProcessor  # noqa: PLC0415
    from sdpj.drivers.llm_registry import LLMRegistry  # noqa: PLC0415
    from sdpj.drivers.llm_service import LLMService  # noqa: PLC0415
    from sdpj.drivers.user_center import UserCenter  # noqa: PLC0415
    from sdpj.infrastructure.config.settings import get_settings  # noqa: PLC0415
    from sdpj.infrastructure.database.result_db import (  # noqa: PLC0415
        ResultDB,
    )
    from sdpj.infrastructure.database.result_db import (  # noqa: PLC0415
        SessionManager as ResultDBSessionManager,
    )
    from sdpj.infrastructure.database.sample_db import (  # noqa: PLC0415
        SampleDB,
        SampleDBSessionManager,
    )
    from sdpj.infrastructure.database.user_db import UserDB, UserDBSessionManager  # noqa: PLC0415
    from sdpj.infrastructure.llm_adapters.llm_adapter_lib import LLMAdapterLib  # noqa: PLC0415
    from sdpj.infrastructure.utils.utils_lib import UtilsLib  # noqa: PLC0415

    cfg = get_settings()

    from sqlalchemy import event as _event  # noqa: PLC0415
    from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415
    from sqlalchemy.pool import NullPool, StaticPool  # noqa: PLC0415

    _is_memory = ":memory:" in cfg.db_url
    _engine = create_async_engine(
        cfg.db_url,
        poolclass=StaticPool if _is_memory else NullPool,
        connect_args={"check_same_thread": False},
    )
    if "sqlite" in cfg.db_url:

        @_event.listens_for(_engine.sync_engine, "connect")
        def _enable_fk(dbapi_conn, connection_record) -> None:  # noqa: ANN001, ARG001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    utils = UtilsLib()
    adapter_lib = LLMAdapterLib()
    sample_sm = SampleDBSessionManager(cfg.db_url, engine=_engine)
    result_sm = ResultDBSessionManager(cfg.db_url, engine=_engine)
    user_sm = UserDBSessionManager(cfg.db_url, engine=_engine)

    from sdpj.infrastructure.database.sample_db.builtin_datasets import (  # noqa: PLC0415
        load_builtin_datasets,
    )

    async def _init_db(skip_builtin_datasets: bool = False) -> None:  # noqa: FBT001, FBT002
        await user_sm.create_tables()
        await sample_sm.create_tables()
        await result_sm.create_tables()
        if not skip_builtin_datasets:
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
        detector=SDPJDetector(dp, cast("LLMServiceInterface", llm)),
        event_logger=EventLogger(
            result_db=result_db, output_targets={"memory", "database"},
        ),
        task_queue_manager=TaskQueueManager(session_manager=result_sm, persistence=result_db),
        db_initializer=_init_db,
        engine=_engine,
    )
