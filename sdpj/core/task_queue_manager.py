"""
TaskQueueManager 实现

该模块实现了任务队列管理的核心功能，支持数据库持久化。
"""
import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from .task_queue_manager_interface import Task, TaskQueueManagerInterface, TaskStatus


class TaskQueueManager:
    """
    任务队列管理器

    负责管理检测任务的入队、出队、状态跟踪。
    使用 asyncio.Queue 实现 FIFO 队列，同时持久化到数据库。
    """

    def __init__(self, session_manager=None):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, Task] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._session_manager = session_manager
        self._initialized = False
        self._poc_progress: Dict[str, dict] = {}
        self._task_progress: Dict[str, dict] = {}
        self._dynamic_progress: Dict[str, dict] = {}

    async def initialize(self) -> None:
        if self._initialized:
            return
        if self._session_manager is None:
            self._initialized = True
            return

        from sdpj.infrastructure.database.result_db.result_db import ResultDB
        from sdpj.infrastructure.database.result_db.session import SessionManager
        if not isinstance(self._session_manager, SessionManager):
            self._initialized = True
            return

        result_db = ResultDB(self._session_manager)
        try:
            non_terminal = await result_db.list_non_terminal_tasks()
        except Exception:
            self._initialized = True
            return

        valid_group_ids: set[str] | None = None
        try:
            tg_ids_in_tasks: set[str] = set()
            for row in non_terminal:
                tg_id = row.get("task_group_id")
                if tg_id:
                    tg_ids_in_tasks.add(tg_id)
            if tg_ids_in_tasks:
                existing_groups = await result_db.list_task_groups()
                existing_ids = {g["task_group_id"] for g in existing_groups}
                valid_group_ids = tg_ids_in_tasks & existing_ids
        except Exception:
            valid_group_ids = None

        for row in non_terminal:
            task_id = row["task_id"]
            tg_id = row.get("task_group_id")
            if valid_group_ids is not None and tg_id and tg_id not in valid_group_ids:
                continue
            status_str = row["task_status"]
            algorithm_type = row.get("algorithm_type", "static")

            if status_str == "running":
                status = TaskStatus.PENDING
            else:
                try:
                    status = TaskStatus(status_str)
                except ValueError:
                    status = TaskStatus.PENDING

            metadata = row.get("metadata_json") or {}
            if "task_group_id" not in metadata:
                metadata["task_group_id"] = row["task_group_id"]

            task = Task(
                task_id=task_id,
                user_id=str(row.get("user_id", "")),
                model_id=row.get("model_id", ""),
                algorithm_type=algorithm_type,
                dataset_id=str(row.get("dataset_id", "")),
                status=status,
                metadata=metadata,
            )

            async with self._lock:
                self._tasks[task_id] = task
                await self._queue.put(task)

            if status_str == "running":
                await self._persist_status(task_id, TaskStatus.PENDING)

        self._initialized = True

    async def enqueue_task(self, task_desc: dict) -> str:
        required_fields = ["user_id", "model_id", "algorithm_type", "dataset_id"]
        for field in required_fields:
            if field not in task_desc:
                raise ValueError(f"任务描述缺少必需字段: {field}")

        task_id = str(uuid.uuid4())
        metadata = task_desc.get("metadata", {})
        task_group_id = metadata.get("task_group_id", task_id)

        task = Task(
            task_id=task_id,
            user_id=task_desc["user_id"],
            model_id=task_desc["model_id"],
            algorithm_type=task_desc["algorithm_type"],
            dataset_id=task_desc["dataset_id"],
            status=TaskStatus.PENDING,
            metadata=metadata
        )

        async with self._lock:
            await self._queue.put(task)
            self._tasks[task_id] = task

        await self._persist_task(task, task_group_id)

        return task_id

    async def dequeue_task(self) -> Task | None:
        while True:
            try:
                task = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return None

            async with self._lock:
                stored = self._tasks.get(task.task_id)
                if stored is None:
                    continue
                if stored.status == TaskStatus.CANCELLED:
                    continue
                stored.status = TaskStatus.RUNNING
                task.status = TaskStatus.RUNNING

            await self._persist_status(task.task_id, TaskStatus.RUNNING)
            return task

    async def dequeue_tasks(self, count: int) -> list[Task]:
        tasks = []
        for _ in range(count):
            task = await self.dequeue_task()
            if task is None:
                break
            tasks.append(task)
        return tasks

    async def update_task_status(self, task_id: str, status: TaskStatus, error_message: str = "") -> bool:
        async with self._lock:
            if task_id not in self._tasks:
                return False
            current = self._tasks[task_id]
            if current.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            current.status = status
            if error_message:
                current.error_message = error_message

        await self._persist_status(task_id, status, error_message)
        return True

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    async def cancel_task(self, task_id: str) -> bool:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            task.status = TaskStatus.CANCELLED

        await self._persist_status(task_id, TaskStatus.CANCELLED)
        return True

    async def remove_task(self, task_id: str) -> bool:
        async with self._lock:
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
        return True

    async def get_queue_view(self) -> list[Task]:
        async with self._lock:
            return list(self._tasks.values())

    async def update_poc_progress(self, task_group_id: str, progress: dict) -> None:
        async with self._lock:
            self._poc_progress[task_group_id] = progress

    async def get_poc_progress(self, task_group_id: str) -> dict | None:
        async with self._lock:
            return self._poc_progress.get(task_group_id)

    async def clear_poc_progress(self, task_group_id: str) -> None:
        async with self._lock:
            self._poc_progress.pop(task_group_id, None)

    async def update_task_progress(self, task_id: str, processed: int, total: int) -> None:
        async with self._lock:
            existing = self._task_progress.get(task_id, {})
            now = time.monotonic()
            start_time = existing.get("start_time")
            if start_time is None:
                start_time = now
            recent_speeds = existing.get("recent_speeds", [])
            last_processed = existing.get("processed", 0)
            last_update_time = existing.get("last_update_time")
            if last_update_time is not None and processed > last_processed:
                elapsed = now - last_update_time
                if elapsed > 0:
                    speed = (processed - last_processed) / elapsed
                    recent_speeds.append(speed)
                    if len(recent_speeds) > 5:
                        recent_speeds = recent_speeds[-5:]
            self._task_progress[task_id] = {
                "processed": processed,
                "total": total,
                "start_time": start_time,
                "last_update_time": now,
                "recent_speeds": recent_speeds,
            }

    async def get_task_progress(self, task_id: str) -> dict | None:
        async with self._lock:
            return self._task_progress.get(task_id)

    async def clear_task_progress(self, task_id: str) -> None:
        async with self._lock:
            self._task_progress.pop(task_id, None)

    async def update_dynamic_progress(self, task_group_id: str, progress: dict) -> None:
        async with self._lock:
            existing = self._dynamic_progress.get(task_group_id, {})
            now = time.monotonic()
            start_time = existing.get("start_time")
            if start_time is None:
                start_time = now
            recent_speeds = existing.get("recent_speeds", [])
            last_processed = existing.get("processed", 0)
            last_update_time = existing.get("last_update_time")
            processed = progress.get("processed", 0)
            if last_update_time is not None and processed > last_processed:
                elapsed = now - last_update_time
                if elapsed > 0:
                    speed = (processed - last_processed) / elapsed
                    recent_speeds.append(speed)
                    if len(recent_speeds) > 5:
                        recent_speeds = recent_speeds[-5:]
            self._dynamic_progress[task_group_id] = {
                "processed": processed,
                "total": progress.get("total", 0),
                "avg_iterations": progress.get("avg_iterations", 0.0),
                "start_time": start_time,
                "last_update_time": now,
                "recent_speeds": recent_speeds,
            }

    async def get_dynamic_progress(self, task_group_id: str) -> dict | None:
        async with self._lock:
            return self._dynamic_progress.get(task_group_id)

    async def clear_dynamic_progress(self, task_group_id: str) -> None:
        async with self._lock:
            self._dynamic_progress.pop(task_group_id, None)

    async def _persist_task(self, task: Task, task_group_id: str) -> None:
        if self._session_manager is None:
            return
        try:
            from sdpj.infrastructure.database.result_db.result_db import ResultDB
            result_db = ResultDB(self._session_manager)

            try:
                await result_db.get_task_group(task_group_id)
            except ValueError:
                try:
                    await result_db.create_task_group_with_id(
                        task_group_id=task_group_id,
                        user_id=int(task.user_id) if task.user_id.isdigit() else 0,
                        model_id=task.model_id,
                    )
                except Exception:
                    pass
        except Exception:
            pass

    async def _persist_status(self, task_id: str, status: TaskStatus, error_message: str = "") -> None:
        if self._session_manager is None:
            return
        try:
            from sdpj.infrastructure.database.result_db.result_db import ResultDB
            result_db = ResultDB(self._session_manager)
            end_time = None
            kwargs: dict = {}
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                end_time = datetime.now(timezone.utc)
            if error_message:
                kwargs["error_message"] = error_message
            await result_db.update_task_status(task_id, status.value, end_time, **kwargs)
        except Exception:
            pass
