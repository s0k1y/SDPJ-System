"""
TaskQueueManager 单元测试
"""

import asyncio
import pytest

from sdpj.core.task_queue_manager import TaskQueueManager
from sdpj.core.task_queue_manager_interface import TaskStatus


@pytest.mark.asyncio
class TestTaskEnqueue:
    """测试任务入队"""

    async def test_enqueue_task_success(self):
        """测试成功入队单个任务"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)

        assert task_id is not None
        assert isinstance(task_id, str)

        # 验证任务状态
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.PENDING

    async def test_enqueue_task_missing_field(self):
        """测试入队任务缺少必需字段"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            # 缺少 algorithm_type 和 dataset_id
        }

        with pytest.raises(ValueError, match="任务描述缺少必需字段"):
            await manager.enqueue_task(task_desc)

    async def test_enqueue_multiple_tasks(self):
        """测试连续入队多个任务"""
        manager = TaskQueueManager()
        task_ids = []

        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            task_id = await manager.enqueue_task(task_desc)
            task_ids.append(task_id)

        # 验证所有任务ID唯一
        assert len(task_ids) == len(set(task_ids))

        # 验证所有任务状态为 PENDING
        for task_id in task_ids:
            status = await manager.get_task_status(task_id)
            assert status == TaskStatus.PENDING


@pytest.mark.asyncio
class TestTaskDequeue:
    """测试任务出队"""

    async def test_dequeue_task_success(self):
        """测试成功出队单个任务"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        task = await manager.dequeue_task()

        assert task is not None
        assert task.task_id == task_id
        assert task.status == TaskStatus.RUNNING

    async def test_dequeue_task_empty_queue(self):
        """测试空队列出队"""
        manager = TaskQueueManager()
        task = await manager.dequeue_task()

        assert task is None

    async def test_dequeue_task_fifo_order(self):
        """测试 FIFO 顺序"""
        manager = TaskQueueManager()
        task_ids = []

        # 入队 3 个任务
        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            task_id = await manager.enqueue_task(task_desc)
            task_ids.append(task_id)

        # 出队并验证顺序
        for expected_id in task_ids:
            task = await manager.dequeue_task()
            assert task.task_id == expected_id


@pytest.mark.asyncio
class TestTaskDequeueMultiple:
    """测试批量出队"""

    async def test_dequeue_tasks_success(self):
        """测试成功并发出队多个任务"""
        manager = TaskQueueManager()

        # 入队 5 个任务
        for i in range(5):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            await manager.enqueue_task(task_desc)

        # 并发出队 3 个任务
        tasks = await manager.dequeue_tasks(3)

        assert len(tasks) == 3
        for task in tasks:
            assert task.status == TaskStatus.RUNNING

    async def test_dequeue_tasks_exceeds_queue_size(self):
        """测试请求数量超过队列大小"""
        manager = TaskQueueManager()

        # 入队 2 个任务
        for i in range(2):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            await manager.enqueue_task(task_desc)

        # 请求出队 5 个任务
        tasks = await manager.dequeue_tasks(5)

        assert len(tasks) == 2

    async def test_dequeue_tasks_empty_queue(self):
        """测试空队列批量出队"""
        manager = TaskQueueManager()
        tasks = await manager.dequeue_tasks(3)

        assert len(tasks) == 0


@pytest.mark.asyncio
class TestTaskStatusUpdate:
    """测试任务状态更新"""

    async def test_update_task_status_success(self):
        """测试成功更新任务状态"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()

        # 更新状态为 COMPLETED
        result = await manager.update_task_status(task_id, TaskStatus.COMPLETED)
        assert result is True

        # 验证状态已更新
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

    async def test_update_task_status_nonexistent(self):
        """测试更新不存在的任务"""
        manager = TaskQueueManager()
        result = await manager.update_task_status("nonexistent", TaskStatus.COMPLETED)

        assert result is False

    async def test_update_task_status_to_failed(self):
        """测试更新任务状态为异常中断"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()

        # 更新状态为 FAILED
        result = await manager.update_task_status(task_id, TaskStatus.FAILED)
        assert result is True

        # 验证状态已更新
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.FAILED


@pytest.mark.asyncio
class TestTaskStatusQuery:
    """测试任务状态查询"""

    async def test_get_task_status_success(self):
        """测试成功查询任务状态"""
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        status = await manager.get_task_status(task_id)

        assert status == TaskStatus.PENDING

    async def test_get_task_status_nonexistent(self):
        """测试查询不存在的任务"""
        manager = TaskQueueManager()
        status = await manager.get_task_status("nonexistent")

        assert status is None


@pytest.mark.asyncio
class TestQueueView:
    """测试队列视图"""

    async def test_get_queue_view_empty(self):
        """测试查询空队列"""
        manager = TaskQueueManager()
        view = await manager.get_queue_view()

        assert len(view) == 0

    async def test_get_queue_view_with_tasks(self):
        """测试查询非空队列"""
        manager = TaskQueueManager()

        # 入队 3 个任务
        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            await manager.enqueue_task(task_desc)

        view = await manager.get_queue_view()

        assert len(view) == 3
        for task in view:
            assert task.status == TaskStatus.PENDING

    async def test_get_queue_view_with_different_statuses(self):
        """测试队列视图包含不同状态的任务"""
        manager = TaskQueueManager()

        # 入队 3 个任务
        task_ids = []
        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            task_id = await manager.enqueue_task(task_desc)
            task_ids.append(task_id)

        # 出队 1 个任务（状态变为 RUNNING）
        await manager.dequeue_task()

        # 更新 1 个任务为 COMPLETED
        await manager.update_task_status(task_ids[1], TaskStatus.COMPLETED)

        view = await manager.get_queue_view()

        assert len(view) == 3
        statuses = [task.status for task in view]
        assert TaskStatus.RUNNING in statuses
        assert TaskStatus.COMPLETED in statuses
        assert TaskStatus.PENDING in statuses


@pytest.mark.asyncio
class TestConcurrency:
    """测试并发场景"""

    async def test_concurrent_enqueue(self):
        """测试并发入队"""
        manager = TaskQueueManager()

        async def enqueue_task(i):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            return await manager.enqueue_task(task_desc)

        # 并发入队 10 个任务
        task_ids = await asyncio.gather(*[enqueue_task(i) for i in range(10)])

        assert len(task_ids) == 10
        assert len(set(task_ids)) == 10  # 所有ID唯一

    async def test_concurrent_dequeue(self):
        """测试并发出队"""
        manager = TaskQueueManager()

        # 入队 10 个任务
        for i in range(10):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            await manager.enqueue_task(task_desc)

        # 并发出队
        tasks = await asyncio.gather(*[manager.dequeue_task() for _ in range(10)])

        # 验证所有任务都被取出
        assert all(task is not None for task in tasks)
        assert len(set(task.task_id for task in tasks)) == 10


@pytest.mark.asyncio
class TestTaskCancel:
    """测试任务取消"""

    async def test_cancel_pending_task(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        result = await manager.cancel_task(task_id)

        assert result is True
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.CANCELLED

    async def test_cancel_running_task(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()

        result = await manager.cancel_task(task_id)

        assert result is True
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.CANCELLED

    async def test_cancel_completed_task_fails(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()
        await manager.update_task_status(task_id, TaskStatus.COMPLETED)

        result = await manager.cancel_task(task_id)

        assert result is False
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

    async def test_cancel_nonexistent_task_fails(self):
        manager = TaskQueueManager()
        result = await manager.cancel_task("nonexistent")

        assert result is False

    async def test_cancel_already_cancelled_task_fails(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.cancel_task(task_id)

        result = await manager.cancel_task(task_id)

        assert result is False


@pytest.mark.asyncio
class TestRemoveTask:
    """测试从队列中移除任务"""

    async def test_remove_pending_task(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        result = await manager.remove_task(task_id)

        assert result is True
        status = await manager.get_task_status(task_id)
        assert status is None

        view = await manager.get_queue_view()
        assert len(view) == 0

    async def test_remove_completed_task(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()
        await manager.update_task_status(task_id, TaskStatus.COMPLETED)

        result = await manager.remove_task(task_id)

        assert result is True
        status = await manager.get_task_status(task_id)
        assert status is None

    async def test_remove_nonexistent_task_fails(self):
        manager = TaskQueueManager()
        result = await manager.remove_task("nonexistent")

        assert result is False

    async def test_remove_task_not_in_queue_view(self):
        manager = TaskQueueManager()

        task_ids = []
        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            task_id = await manager.enqueue_task(task_desc)
            task_ids.append(task_id)

        await manager.remove_task(task_ids[1])

        view = await manager.get_queue_view()
        assert len(view) == 2
        view_ids = [t.task_id for t in view]
        assert task_ids[1] not in view_ids


@pytest.mark.asyncio
class TestTerminalStateProtection:
    """测试终态保护：已处于终态的任务状态不可被覆盖"""

    async def test_update_status_does_not_overwrite_cancelled(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()
        await manager.cancel_task(task_id)

        result = await manager.update_task_status(task_id, TaskStatus.COMPLETED)

        assert result is False
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.CANCELLED

    async def test_update_status_does_not_overwrite_completed(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()
        await manager.update_task_status(task_id, TaskStatus.COMPLETED)

        result = await manager.update_task_status(task_id, TaskStatus.RUNNING)

        assert result is False
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

    async def test_update_status_does_not_overwrite_failed(self):
        manager = TaskQueueManager()
        task_desc = {
            "user_id": "user1",
            "model_id": "gpt-4",
            "algorithm_type": "static",
            "dataset_id": "dataset1",
        }

        task_id = await manager.enqueue_task(task_desc)
        await manager.dequeue_task()
        await manager.update_task_status(task_id, TaskStatus.FAILED)

        result = await manager.update_task_status(task_id, TaskStatus.COMPLETED)

        assert result is False
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.FAILED

    async def test_cancelled_task_skipped_on_dequeue(self):
        manager = TaskQueueManager()

        task_ids = []
        for i in range(3):
            task_desc = {
                "user_id": f"user{i}",
                "model_id": "gpt-4",
                "algorithm_type": "static",
                "dataset_id": "dataset1",
            }
            task_id = await manager.enqueue_task(task_desc)
            task_ids.append(task_id)

        await manager.cancel_task(task_ids[1])

        dequeued = []
        for _ in range(3):
            task = await manager.dequeue_task()
            if task:
                dequeued.append(task.task_id)

        assert task_ids[1] not in dequeued
        assert task_ids[0] in dequeued
        assert task_ids[2] in dequeued
