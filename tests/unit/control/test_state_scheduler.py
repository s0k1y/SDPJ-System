"""StateScheduler 单元测试 — 聚焦 start_detection 状态守卫逻辑"""

import asyncio
import pytest

from sdpj.control.state_scheduler import StateScheduler
from sdpj.control.system_states import SystemStateMachine
from sdpj.core.task_queue_manager import TaskQueueManager
from sdpj.core.task_queue_manager_interface import TaskStatus
from tests.fixtures.sample_data import REAL_MODEL_ID, REAL_MODEL_ID_2
from typing import Any


class _StubAccountManager:
    async def authenticate(self, *a: Any, **kw: Any) -> None:
        return {"success": True}


class _StubDACManager:
    async def check_access(self, *a: Any, **kw: Any) -> None:
        return True


class _StubConfigManager:
    async def read_config(self, *a: Any, **kw: Any) -> None:
        return None

    async def query_datasets(self, *a: Any, **kw: Any) -> None:
        return []

    async def is_model_available(self, model_id: Any) -> None:
        return (True, None)

    async def initialize_registry(self) -> None:
        pass

    async def shutdown_registry(self) -> None:
        pass

    async def register_private_model(self, *a: Any, **kw: Any) -> None:
        return (True, None, None)


class _StubReportManager:
    pass


class _StubDetector:
    pass


class _StubEventLogger:
    def log_operation(self, *a: Any, **kw: Any) -> None:
        pass

    def log_runtime(self, *a: Any, **kw: Any) -> None:
        pass

    def log_error(self, *a: Any, **kw: Any) -> None:
        pass


def _make_scheduler() -> StateScheduler:
    return StateScheduler(
        account_manager=_StubAccountManager(),
        dac_manager=_StubDACManager(),
        config_manager=_StubConfigManager(),
        report_manager=_StubReportManager(),
        detector=_StubDetector(),
        event_logger=_StubEventLogger(),
        task_queue_manager=TaskQueueManager(),
    )


def _state_val(scheduler: StateScheduler) -> str:
    return scheduler.get_system_state()


@pytest.mark.asyncio
class TestStartDetectionStateGuard:
    """BUG: 检测中时新任务应可入队"""

    async def test_idle_state_allows_start_detection(self) -> None:
        """idle 状态下 start_detection 应成功并转为 detecting"""
        scheduler = _make_scheduler()
        assert _state_val(scheduler) == "idle"

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )

        assert result["success"] is True
        assert _state_val(scheduler) == "detecting"


class _StubReportManagerForDelete:
    def __init__(self, existing_groups: Any=None) -> None:
        self._existing_groups = existing_groups or []
        self._deleted = False

    async def delete_report(self, **kwargs: Any) -> None:
        self._deleted = True
        return (True, "")

    async def list_reports(self, **kwargs: Any) -> None:
        if self._deleted:
            return [
                g
                for g in self._existing_groups
                if g["task_group_id"] not in kwargs.get("_deleted_ids", set())
            ]
        return list(self._existing_groups)


class _StubConfigManagerWithDatasets:
    async def read_config(self, *a: Any, **kw: Any) -> None:
        return None

    async def query_datasets(self, *a: Any, **kw: Any) -> None:
        return []

    async def read_configs_batch(self, ids: Any) -> None:
        return {}

    async def is_model_available(self, model_id: Any) -> None:
        return (True, None)

    async def initialize_registry(self) -> None:
        pass

    async def shutdown_registry(self) -> None:
        pass

    async def register_private_model(self, *a: Any, **kw: Any) -> None:
        return (True, None, None)


class _StubEventLoggerWithLog:
    def log_operation(self, *a: Any, **kw: Any) -> None:
        pass

    def log_runtime(self, *a: Any, **kw: Any) -> None:
        pass

    def log_error(self, *a: Any, **kw: Any) -> None:
        pass


def _make_scheduler_with_stubs(report_mgr: Any=None) -> StateScheduler:
    return StateScheduler(
        account_manager=_StubAccountManager(),
        dac_manager=_StubDACManager(),
        config_manager=_StubConfigManagerWithDatasets(),
        report_manager=report_mgr or _StubReportManagerForDelete(),
        detector=_StubDetector(),
        event_logger=_StubEventLoggerWithLog(),
        task_queue_manager=TaskQueueManager(),
    )


@pytest.mark.asyncio
class TestDeleteReportSyncsTaskQueue:
    """BUG修复: 删除报告后仪表盘任务队列应同步清理"""

    async def test_delete_task_group_removes_from_queue(self) -> None:
        """删除任务组报告后,内存队列中对应任务应被移除"""
        scheduler = _make_scheduler_with_stubs()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        assert result["success"] is True
        task_group_id = result["task_group_id"]

        for tid in result["task_ids"]:
            await scheduler._task_queue.update_task_status(tid, TaskStatus.COMPLETED)

        queue_view = await scheduler._task_queue.get_queue_view()
        assert any(t.metadata.get("task_group_id") == task_group_id for t in queue_view)

        delete_result = await scheduler.delete_report(task_group_id, 1, "task_group")
        assert delete_result["success"] is True

        queue_view_after = await scheduler._task_queue.get_queue_view()
        assert not any(t.metadata.get("task_group_id") == task_group_id for t in queue_view_after)

    async def test_delete_single_task_removes_from_queue(self) -> None:
        """删除单个任务报告后,内存队列中对应任务应被移除"""
        scheduler = _make_scheduler_with_stubs()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1, 2],
            },
        )
        assert result["success"] is True
        task_id = result["task_ids"][0]

        await scheduler._task_queue.update_task_status(task_id, TaskStatus.COMPLETED)

        delete_result = await scheduler.delete_report(task_id, 1, "task")
        assert delete_result["success"] is True

        queue_view = await scheduler._task_queue.get_queue_view()
        assert not any(t.task_id == task_id for t in queue_view)

    async def test_orphan_completed_group_cleaned_on_progress_query(self) -> None:
        """孤儿任务组(数据库已删除但内存残留)在查询进度时应被自动清理"""
        existing_groups = [{"task_group_id": "other-group"}]
        report_mgr = _StubReportManagerForDelete(existing_groups=existing_groups)
        scheduler = _make_scheduler_with_stubs(report_mgr=report_mgr)

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        task_group_id = result["task_group_id"]

        for tid in result["task_ids"]:
            await scheduler._task_queue.update_task_status(tid, TaskStatus.COMPLETED)

        queue_view = await scheduler._task_queue.get_queue_view()
        assert any(t.metadata.get("task_group_id") == task_group_id for t in queue_view)

        progress = await scheduler.query_detection_progress()
        assert progress["success"] is True

        orphan_group_ids = [g["task_group_id"] for g in progress["groups"]]
        assert task_group_id not in orphan_group_ids

        queue_view_after = await scheduler._task_queue.get_queue_view()
        assert not any(t.metadata.get("task_group_id") == task_group_id for t in queue_view_after)

    async def test_running_group_not_cleaned_as_orphan(self) -> None:
        """运行中的任务组不应被孤儿清理逻辑误删"""
        existing_groups = []
        report_mgr = _StubReportManagerForDelete(existing_groups=existing_groups)
        scheduler = _make_scheduler_with_stubs(report_mgr=report_mgr)

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        task_group_id = result["task_group_id"]

        progress = await scheduler.query_detection_progress()
        assert progress["success"] is True

        group_ids = [g["task_group_id"] for g in progress["groups"]]
        assert task_group_id in group_ids

    async def test_delete_report_cleanup_exception_does_not_fail_delete(self) -> None:
        """清理任务队列异常不应导致删除报告操作失败"""
        scheduler = _make_scheduler_with_stubs()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        task_group_id = result["task_group_id"]

        original_cleanup = scheduler._cleanup_task_queue_after_report_delete

        async def failing_cleanup(target_id: Any, granularity: Any) -> None:
            raise RuntimeError("simulated cleanup failure")

        scheduler._cleanup_task_queue_after_report_delete = failing_cleanup

        delete_result = await scheduler.delete_report(task_group_id, 1, "task_group")
        assert delete_result["success"] is True

    async def test_detecting_state_allows_enqueue(self) -> None:
        """detecting 状态下 start_detection 应允许新任务入队(核心BUG修复验证)"""
        scheduler = _make_scheduler()

        result1 = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        assert result1["success"] is True
        assert _state_val(scheduler) == "detecting"

        result2 = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [2],
            },
        )
        assert result2["success"] is True
        assert result2["task_group_id"] is not None
        assert len(result2["task_ids"]) == 1
        assert _state_val(scheduler) == "detecting"

    async def test_detecting_state_multiple_enqueue(self) -> None:
        """detecting 状态下连续多次入队均应成功"""
        scheduler = _make_scheduler()

        await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )

        for i in range(3):
            result = await scheduler.start_detection(
                1,
                {
                    "model_id": REAL_MODEL_ID,
                    "detection_type": "static",
                    "dataset_ids": [10 + i],
                },
            )
            assert result["success"] is True, f"第{i + 1}次入队应成功"

    async def test_generating_report_state_rejects_detection(self) -> None:
        """generating_report 状态下应拒绝启动检测"""
        scheduler = _make_scheduler()
        scheduler._fsm.start_report()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )

        assert result["success"] is False
        assert "不允许" in result["error"]

    async def test_error_state_rejects_detection(self) -> None:
        """error 状态下应拒绝启动检测"""
        scheduler = _make_scheduler()
        scheduler._fsm.to_error()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )

        assert result["success"] is False
        assert "不允许" in result["error"]

    async def test_configuring_state_rejects_detection(self) -> None:
        """configuring 状态下应拒绝启动检测"""
        scheduler = _make_scheduler()
        scheduler._fsm.start_configuring()

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )

        assert result["success"] is False
        assert "不允许" in result["error"]

    async def test_idle_to_detecting_back_to_idle_then_enqueue(self) -> None:
        """idle→detecting→idle 后应能正常再次入队"""
        scheduler = _make_scheduler()

        await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        assert _state_val(scheduler) == "detecting"

        scheduler._fsm.detection_done()
        assert _state_val(scheduler) == "idle"

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [2],
            },
        )
        assert result["success"] is True
        assert _state_val(scheduler) == "detecting"


@pytest.mark.asyncio
class TestMultiEncodingTaskSplit:
    """多编码间接注入: 数据集×编码 双重循环拆分逻辑"""

    async def test_direct_only_creates_one_task_per_dataset(self) -> None:
        """has_direct=True, encoding_types=[] 时每个数据集创建 1 个直接注入任务"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1, 2],
                "encoding_types": [],
                "has_direct": True,
            },
        )
        assert result["success"] is True
        assert len(result["task_ids"]) == 2

    async def test_encoding_only_creates_tasks_per_encoding(self) -> None:
        """has_direct=False, encoding_types=['base64','hex'] 时每个数据集创建 2 个任务"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1, 2],
                "encoding_types": ["base64", "hex"],
                "has_direct": False,
            },
        )
        assert result["success"] is True
        assert len(result["task_ids"]) == 4  # 2 datasets x 2 encodings

    async def test_direct_plus_encodings_creates_correct_count(self) -> None:
        """has_direct=True, encoding_types=['base64','caesar'] 时任务数 = N_ds x (1 + len(enc))"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1, 2, 3],
                "encoding_types": ["base64", "caesar"],
                "has_direct": True,
            },
        )
        assert result["success"] is True
        assert len(result["task_ids"]) == 9  # 3 datasets x (1 direct + 2 encodings)

    async def test_task_metadata_contains_encoding_type_and_attack_path(self) -> None:
        """每个子任务的 metadata 应包含 encoding_type 和 attack_path"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
                "encoding_types": ["base64"],
                "has_direct": True,
            },
        )
        assert result["success"] is True
        queue_view = await scheduler._task_queue.get_queue_view()
        tasks = [t for t in queue_view if t.metadata.get("task_group_id") == result["task_group_id"]]
        assert len(tasks) == 2

        direct_task = next(t for t in tasks if t.metadata.get("encoding_type") is None)
        assert direct_task.metadata["attack_path"] == "direct"

        encoded_task = next(t for t in tasks if t.metadata.get("encoding_type") == "base64")
        assert encoded_task.metadata["attack_path"] == "indirect:multi-encoding:base64"

    async def test_single_dataset_multiple_encodings(self) -> None:
        """单数据集 + 多编码应创建正确数量的任务"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
                "encoding_types": ["base64", "hex", "rot13"],
                "has_direct": False,
            },
        )
        assert result["success"] is True
        assert len(result["task_ids"]) == 3

        queue_view = await scheduler._task_queue.get_queue_view()
        tasks = [t for t in queue_view if t.metadata.get("task_group_id") == result["task_group_id"]]
        enc_types = {t.metadata.get("encoding_type") for t in tasks}
        assert enc_types == {"base64", "hex", "rot13"}

    async def test_no_encoding_types_defaults_to_direct_only(self) -> None:
        """未传 encoding_types 时默认 has_direct=True, 行为与原有一致"""
        scheduler = _make_scheduler()
        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
            },
        )
        assert result["success"] is True
        assert len(result["task_ids"]) == 1

        queue_view = await scheduler._task_queue.get_queue_view()
        task = next(t for t in queue_view if t.task_id == result["task_ids"][0])
        assert task.metadata.get("encoding_type") is None
        assert task.metadata.get("attack_path") == "direct"

    async def test_concurrent_tasks_pass_encoding_type_to_detector(self) -> None:
        """execute_concurrent_tasks 从 metadata 提取 encoding_type 并透传"""
        scheduler = _make_scheduler()

        captured_params: list[dict] = []

        async def mock_execute(task_id: str, task_params: dict) -> dict:
            captured_params.append(task_params)
            return {"success": True, "task_id": task_id, "result": {"status": "completed"}}

        scheduler.execute_detection_task = mock_execute  # type: ignore[method-assign]

        result = await scheduler.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": [1],
                "encoding_types": ["base64", "hex"],
                "has_direct": False,
            },
        )
        assert result["success"] is True

        await scheduler.execute_concurrent_tasks(max_concurrency=3)

        enc_types_passed = {p.get("encoding_type") for p in captured_params}
        assert enc_types_passed == {"base64", "hex"}
