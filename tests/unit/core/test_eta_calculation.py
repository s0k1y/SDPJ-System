import asyncio
import time
import pytest
from sdpj.core.task_queue_manager import TaskQueueManager


@pytest.fixture
def tqm():
    return TaskQueueManager()


class TestTaskProgressWithETA:
    @pytest.mark.asyncio
    async def test_first_update_sets_start_time(self, tqm):
        await tqm.update_task_progress("t1", 10, 100)
        prog = await tqm.get_task_progress("t1")
        assert prog["start_time"] is not None
        assert prog["processed"] == 10
        assert prog["total"] == 100
        assert prog["recent_speeds"] == []

    @pytest.mark.asyncio
    async def test_speed_tracking(self, tqm):
        await tqm.update_task_progress("t1", 10, 100)
        await asyncio.sleep(0.05)
        await tqm.update_task_progress("t1", 20, 100)
        prog = await tqm.get_task_progress("t1")
        assert len(prog["recent_speeds"]) == 1
        assert prog["recent_speeds"][0] > 0

    @pytest.mark.asyncio
    async def test_sliding_window_max_5(self, tqm):
        await tqm.update_task_progress("t1", 10, 100)
        for i in range(10):
            await asyncio.sleep(0.01)
            await tqm.update_task_progress("t1", 20 + i * 10, 100)
        prog = await tqm.get_task_progress("t1")
        assert len(prog["recent_speeds"]) <= 5

    @pytest.mark.asyncio
    async def test_clear_task_progress(self, tqm):
        await tqm.update_task_progress("t1", 10, 100)
        await tqm.clear_task_progress("t1")
        prog = await tqm.get_task_progress("t1")
        assert prog is None


class TestDynamicProgressWithETA:
    @pytest.mark.asyncio
    async def test_update_and_get(self, tqm):
        await tqm.update_dynamic_progress(
            "g1", {"processed": 5, "total": 50, "avg_iterations": 2.5}
        )
        prog = await tqm.get_dynamic_progress("g1")
        assert prog["processed"] == 5
        assert prog["total"] == 50
        assert prog["avg_iterations"] == 2.5
        assert prog["start_time"] is not None

    @pytest.mark.asyncio
    async def test_speed_tracking(self, tqm):
        await tqm.update_dynamic_progress(
            "g1", {"processed": 5, "total": 50, "avg_iterations": 2.0}
        )
        await asyncio.sleep(0.05)
        await tqm.update_dynamic_progress(
            "g1", {"processed": 10, "total": 50, "avg_iterations": 2.3}
        )
        prog = await tqm.get_dynamic_progress("g1")
        assert len(prog["recent_speeds"]) == 1
        assert prog["recent_speeds"][0] > 0

    @pytest.mark.asyncio
    async def test_clear_dynamic_progress(self, tqm):
        await tqm.update_dynamic_progress(
            "g1", {"processed": 5, "total": 50, "avg_iterations": 2.5}
        )
        await tqm.clear_dynamic_progress("g1")
        prog = await tqm.get_dynamic_progress("g1")
        assert prog is None

    @pytest.mark.asyncio
    async def test_nonexistent_returns_none(self, tqm):
        prog = await tqm.get_dynamic_progress("nonexistent")
        assert prog is None


class TestPoCProgressWithSubtypeStats:
    @pytest.mark.asyncio
    async def test_subtype_stats_stored(self, tqm):
        subtype_stats = {
            "jailbreakv": {"current": 5, "target": 9, "event_set": False},
            "role_play": {"current": 3, "target": 3, "event_set": True},
        }
        await tqm.update_poc_progress(
            "g1",
            {
                "processed": 800,
                "total": 30276,
                "found": 20,
                "score_counts": {"2": 10, "3": 5, "5": 5},
                "subtype_stats": subtype_stats,
                "remaining_subtypes": ["jailbreakv"],
                "start_time": time.monotonic(),
                "last_update_time": time.monotonic(),
            },
        )
        prog = await tqm.get_poc_progress("g1")
        assert prog["subtype_stats"] == subtype_stats
        assert prog["remaining_subtypes"] == ["jailbreakv"]
        assert prog["start_time"] is not None
