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
    CANCELLED = "cancelled"  # 已取消


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
    error_message: str = ""   # 错误信息（仅 FAILED 状态时有值）


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

    async def update_task_status(self, task_id: str, status: TaskStatus, error_message: str = "") -> bool:
        """
        更新单个任务的执行状态

        Args:
            task_id: 队列任务标识
            status: 新状态（RUNNING/COMPLETED/FAILED）
            error_message: 错误信息（仅 FAILED 状态时使用）

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

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务

        将任务状态标记为 CANCELLED。若任务仍在队列中，出队时会被跳过。

        Args:
            task_id: 队列任务标识

        Returns:
            取消成功返回 True，任务不存在或已终态返回 False
        """
        ...

    async def remove_task(self, task_id: str) -> bool:
        """
        从队列中移除指定任务

        直接从内存中删除任务记录，不再出现在队列视图中。

        Args:
            task_id: 队列任务标识

        Returns:
            移除成功返回 True，任务不存在返回 False
        """
        ...

    async def get_queue_view(self) -> list[Task]:
        """
        查询队列整体视图

        Returns:
            当前队列中全部任务及其状态的列表
        """
        ...

    async def update_poc_progress(self, task_group_id: str, progress: dict) -> None:
        """更新指定任务组的 PoC 池构建进度

        Args:
            task_group_id: 任务组ID
            progress: {"processed": int, "total": int, "found": int, "score_counts": dict}
        """
        ...

    async def get_poc_progress(self, task_group_id: str) -> dict | None:
        """获取指定任务组的 PoC 池构建进度，不存在返回 None"""
        ...

    async def clear_poc_progress(self, task_group_id: str) -> None:
        """清除指定任务组的 PoC 池构建进度"""
        ...

    async def update_dynamic_progress(self, task_group_id: str, progress: dict) -> None:
        """更新指定任务组的动态检测进度

        Args:
            task_group_id: 任务组ID
            progress: {"processed": int, "total": int, "avg_iterations": float}
        """
        ...

    async def get_dynamic_progress(self, task_group_id: str) -> dict | None:
        """获取指定任务组的动态检测进度，不存在返回 None"""
        ...

    async def clear_dynamic_progress(self, task_group_id: str) -> None:
        """清除指定任务组的动态检测进度"""
        ...
