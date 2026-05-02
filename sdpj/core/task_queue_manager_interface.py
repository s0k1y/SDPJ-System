"""
TaskQueueManager 接口定义

该模块定义了任务队列管理的接口契约。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 异常中断


@dataclass
class Task:
    """检测任务数据类"""
    task_id: str              # 队列任务标识
    user_id: str              # 用户ID
    model_id: str             # 目标被测大模型ID
    algorithm_type: str       # 算法类型（"static" 或 "dynamic"）
    dataset_id: str           # 检测数据集标识
    status: TaskStatus        # 任务状态
    metadata: dict            # 其他业务元信息


class TaskQueueManagerInterface(Protocol):
    """
    任务队列管理接口

    该接口定义了任务队列管理的核心能力，被 StateScheduler 调用。
    """

    async def enqueue_task(self, task_desc: dict) -> str:
        """
        接收新检测任务并加入队列尾部

        Args:
            task_desc: 检测任务描述，至少包含：
                - user_id: 用户ID
                - model_id: 目标被测大模型ID
                - algorithm_type: 静态/动态算法类型
                - dataset_id: 选用的检测数据集标识
                - metadata: 其他业务元信息（可选）

        Returns:
            新加入任务对应的队列任务标识

        Raises:
            ValueError: 任务描述缺少必需字段
        """
        ...

    async def dequeue_task(self) -> Task | None:
        """
        按 FIFO 顺序取出下一个待执行任务

        Returns:
            队头任务，如果队列为空则返回 None
        """
        ...

    async def dequeue_tasks(self, count: int) -> list[Task]:
        """
        按 FIFO 顺序并发取出多个待执行任务

        Args:
            count: 目标并发度上限

        Returns:
            从队头起连续若干个任务的列表
        """
        ...

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        更新单个任务的执行状态

        Args:
            task_id: 队列任务标识
            status: 新状态（RUNNING/COMPLETED/FAILED）

        Returns:
            更新成功返回 True，任务不存在返回 False
        """
        ...

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """
        查询单个任务的执行状态

        Args:
            task_id: 队列任务标识

        Returns:
            当前任务状态，任务不存在返回 None
        """
        ...

    async def get_queue_view(self) -> list[Task]:
        """
        查询队列整体视图

        Returns:
            当前队列中全部任务及其状态的列表
        """
        ...
