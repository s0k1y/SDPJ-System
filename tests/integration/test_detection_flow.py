"""检测流程集成测试 — StateScheduler 核心调度"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from sdpj.control.state_scheduler import StateScheduler
from tests.fixtures.sample_data import REAL_MODEL_ID


def _make_scheduler(**overrides):
    config = AsyncMock()
    config.is_model_available = AsyncMock(return_value=(True, MagicMock()))
    config.initialize_registry = AsyncMock(return_value=True)
    config.shutdown_registry = AsyncMock(return_value=True)
    config.register_private_model = AsyncMock(return_value=(True, "m", ""))
    config.read_config = AsyncMock(return_value=None)
    config.query_datasets = AsyncMock(return_value=[])
    defaults = dict(
        account_manager=AsyncMock(),
        dac_manager=AsyncMock(),
        config_manager=config,
        report_manager=AsyncMock(),
        detector=AsyncMock(),
        event_logger=MagicMock(),
        task_queue_manager=AsyncMock(),
    )
    defaults.update(overrides)
    return StateScheduler(**defaults)


@pytest.mark.asyncio
class TestStartDetection:
    async def test_enqueues_tasks_per_dataset(self):
        tq = AsyncMock()
        tq.enqueue_task = AsyncMock(side_effect=["t1", "t2"])
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.start_detection(1, {
            "model_id": REAL_MODEL_ID,
            "detection_type": "static",
            "dataset_ids": ["ds1", "ds2"],
        })
        assert result["success"]
        assert len(result["task_ids"]) == 2
        assert tq.enqueue_task.call_count == 2

    async def test_returns_task_group_id(self):
        tq = AsyncMock()
        tq.enqueue_task = AsyncMock(return_value="tid")
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.start_detection(1, {"model_id": "m", "dataset_ids": ["d1"]})
        assert "task_group_id" in result and result["task_group_id"]


@pytest.mark.asyncio
class TestQueryDetectionProgress:
    async def test_task_not_found(self):
        tq = AsyncMock()
        tq.get_task_status = AsyncMock(return_value=None)
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.query_detection_progress("nonexistent")
        assert not result["success"]

    async def test_task_found(self):
        from sdpj.core.task_queue_manager_interface import TaskStatus
        tq = AsyncMock()
        tq.get_task_status = AsyncMock(return_value=TaskStatus.RUNNING)
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.query_detection_progress("t1")
        assert result["success"] and result["status"] == "running"


@pytest.mark.asyncio
class TestScheduleUserAuth:
    async def test_login_success(self):
        acct = AsyncMock()
        acct.login = AsyncMock(return_value=(True, 42, ""))
        s = _make_scheduler(account_manager=acct)
        result = await s.schedule_user_auth("alice", "pw", "login")
        assert result["success"] and result["user_id"] == 42

    async def test_register_short_password(self):
        acct = AsyncMock()
        acct.register = AsyncMock(return_value=(False, None, "密码长度至少6个字符"))
        s = _make_scheduler(account_manager=acct)
        result = await s.schedule_user_auth("alice", "123", "register")
        assert not result["success"]

    async def test_unknown_action(self):
        s = _make_scheduler()
        result = await s.schedule_user_auth("a", "b", "unknown")
        assert not result["success"]


@pytest.mark.asyncio
class TestGetSystemState:
    async def test_initial_state(self):
        s = _make_scheduler()
        state = s.get_system_state()
        assert isinstance(state, str) and state
