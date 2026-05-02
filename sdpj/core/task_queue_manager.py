"""
TaskQueueManager 实现

该模块实现了任务队列管理的核心功能。
"""
import asyncio
import uuid
from typing import Dict

from .task_queue_manager_interface import Task, TaskQueueManagerInterface, TaskStatus


class TaskQueueManager:
    """
    任务队列管理器

    负责管理检测任务的入队、出队、状态跟踪。
    使用 asyncio.Queue 实现 FIFO 队列，内存存储任务状态。
    """

    def __init__(self):
        """初始化任务队列管理器"""
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, Task] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def enqueue_task(self, task_desc: dict) -> str:
        """
        接收新检测任务并加入队列尾部

        Args:
            task_desc: 检测任务描述

        Returns:
            新加入任务对应的队列任务标识

        Raises:
            ValueError: 任务描述缺少必需字段
        """
        # 验证必需字段
        required_fields = ["user_id", "model_id", "algorithm_type", "dataset_id"]
        for field in required_fields:
            if field not in task_desc:
                raise ValueError(f"任务描述缺少必需字段: {field}")

        # 生成唯一任务标识
        task_id = str(uuid.uuid4())

        # 创建任务对象
        task = Task(
            task_id=task_id,
            user_id=task_desc["user_id"],
            model_id=task_desc["model_id"],
            algorithm_type=task_desc["algorithm_type"],
            dataset_id=task_desc["dataset_id"],
            status=TaskStatus.PENDING,
            metadata=task_desc.get("metadata", {})
        )

        # 加入队列和状态存储
        async with self._lock:
            await self._queue.put(task)
            self._tasks[task_id] = task

        return task_id

    async def dequeue_task(self) -> Task | None:
        """
        按 FIFO 顺序取出下一个待执行任务

        Returns:
            队头任务，如果队列为空则返回 None
        """
        try:
            # 非阻塞取出任务
            task = self._queue.get_nowait()

            # 更新状态为 RUNNING
            async with self._lock:
                if task.task_id in self._tasks:
                    self._tasks[task.task_id].status = TaskStatus.RUNNING
                    task.status = TaskStatus.RUNNING

            return task
        except asyncio.QueueEmpty:
            return None

    async def dequeue_tasks(self, count: int) -> list[Task]:
        """
        按 FIFO 顺序并发取出多个待执行任务

        Args:
            count: 目标并发度上限

        Returns:
            从队头起连续若干个任务的列表
        """
        tasks = []
        for _ in range(count):
            task = await self.dequeue_task()
            if task is None:
                break
            tasks.append(task)
        return tasks

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        更新单个任务的执行状态

        Args:
            task_id: 队列任务标识
            status: 新状态

        Returns:
            更新成功返回 True，任务不存在返回 False
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            self._tasks[task_id].status = status
            return True

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """
        查询单个任务的执行状态

        Args:
            task_id: 队列任务标识

        Returns:
            当前任务状态，任务不存在返回 None
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    async def get_queue_view(self) -> list[Task]:
        """
        查询队列整体视图

        Returns:
            当前队列中全部任务及其状态的列表
        """
        async with self._lock:
            return list(self._tasks.values())
