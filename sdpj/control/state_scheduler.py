"""StateScheduler 系统状态管理及调度控制

依赖模块: AccountManager, DACManager, PrivateConfigManager,
          ReportManager, SDPJDetector, EventLogger, TaskQueueManager
被依赖模块: CLI, WebUI
"""
import asyncio
import time
import uuid
import json
from typing import Callable, Optional

from sdpj.core.account_manager_interface import AccountManagerInterface
from sdpj.core.dac_manager_interface import DACManagerInterface
from sdpj.core.private_config_manager_interface import PrivateConfigManagerInterface
from sdpj.core.report_manager_interface import ReportManagerInterface
from sdpj.core.sdpj_detector_interface import SDPJDetectorInterface
from sdpj.core.event_logger_interface import EventLoggerInterface, LogCategory
from sdpj.core.task_queue_manager_interface import TaskQueueManagerInterface, TaskStatus
from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.drivers.llm_registry_interface import LLMRegistryInterface

from sdpj.control.system_states import SystemStateMachine


class StateScheduler(StateSchedulerInterface):
    """系统状态管理及调度控制"""

    def __init__(
        self,
        account_manager: AccountManagerInterface,
        dac_manager: DACManagerInterface,
        config_manager: PrivateConfigManagerInterface,
        report_manager: ReportManagerInterface,
        detector: SDPJDetectorInterface,
        event_logger: EventLoggerInterface,
        task_queue_manager: TaskQueueManagerInterface,
        llm_registry: LLMRegistryInterface,
        db_initializer=None,
    ):
        self._account = account_manager
        self._dac = dac_manager
        self._config = config_manager
        self._report = report_manager
        self._detector = detector
        self._logger = event_logger
        self._fsm = SystemStateMachine()
        self._task_queue = task_queue_manager
        self._registry = llm_registry
        self._db_initializer = db_initializer
        self._state_callbacks: list = []
        self._error_callbacks: list = []
        self._log_callbacks: list = []
        self._llm_call_callbacks: list = []
        self._consumer_task: asyncio.Task | None = None
        self._enqueue_in_progress: bool = False

    # ── 内部日志辅助 ──

    async def startup(self) -> None:
        if self._db_initializer is not None:
            await self._db_initializer()
        await self._registry.initialize()
        await self._task_queue.initialize()
        self.start_task_consumer()
        if hasattr(self._logger, 'start_db_writer'):
            await self._logger.start_db_writer()
        if hasattr(self._logger, 'subscribe_logs'):
            self._logger.subscribe_logs(self._on_new_log)
        if hasattr(self._logger, 'cleanup_old_logs'):
            await self._logger.cleanup_old_logs()

    async def shutdown(self) -> None:
        if hasattr(self._logger, 'flush'):
            await self._logger.flush()
        if hasattr(self._logger, 'unsubscribe_logs'):
            self._logger.unsubscribe_logs(self._on_new_log)
        await self.stop_task_consumer()
        await self._registry.shutdown()

    # ── 后台任务消费者 ──

    def start_task_consumer(self, interval: float = 2.0, max_concurrency: int = 3) -> None:
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = asyncio.create_task(
                self._consume_loop(interval, max_concurrency)
            )
            self._log_rt("consumer_started", f"后台任务消费者已启动 (间隔={interval}s, 并发={max_concurrency})")

    async def stop_task_consumer(self) -> None:
        if self._consumer_task is not None and not self._consumer_task.done():
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._log_rt("consumer_stopped", "后台任务消费者已停止")
        self._consumer_task = None

    async def _consume_loop(self, interval: float, max_concurrency: int) -> None:
        while True:
            try:
                if self.get_system_state() == "detecting":
                    await self.execute_concurrent_tasks(max_concurrency)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._log_err("ConsumerError", f"后台消费者异常: {e}")
            await asyncio.sleep(interval)

    def _log_op(self, user_id: int, op: str, ctx: dict) -> None:
        self._logger.log_operation(str(user_id), op, ctx)

    def _log_rt(self, event: str, desc: str) -> None:
        self._logger.log_runtime("StateScheduler", event, desc)

    def _log_state_transition(self, from_state: str, to_state: str, trigger: str) -> None:
        """记录状态转移日志"""
        self._logger.log_runtime(
            "StateScheduler",
            "state_transition",
            f"状态转移: {from_state} → {to_state} (触发: {trigger})"
        )

    def _log_err(self, err_type: str, desc: str) -> None:
        self._logger.log_error("StateScheduler", err_type, desc)

    # ── 检测调度 (职责 1-4) ──

    async def start_detection(self, user_id: int, config_data: dict) -> dict:
        model_id: str = config_data["model_id"]
        detection_type: str = config_data.get("detection_type", "static")
        dataset_ids: list = config_data.get("dataset_ids", [])
        jailbreak_dataset_ids: list | None = config_data.get("jailbreak_dataset_ids") or None
        max_iterations: int = config_data.get("max_iterations", 3)
        force_refresh: bool = config_data.get("force_refresh", False)
        config_id: int | None = config_data.get("config_id")

        loaded_config = None
        if config_id is not None:
            has_access = await self._dac.check_access(config_id, user_id)
            if not has_access:
                return {"success": False, "error": "无访问权限：无法使用该私有配置"}
            loaded = await self._config.read_config(config_id)
            if loaded:
                dataset_ids = loaded.get("dataset_ids", dataset_ids)
                model_id = loaded.get("model_id", model_id)
                loaded_config = loaded

        available, _ = await self._registry.is_model_available(model_id)
        if not available:
            if loaded_config is not None:
                adapter_content = json.dumps(loaded_config)
                ok, _, err = await self._registry.register_private_model(adapter_content, model_id)
                if not ok:
                    return {"success": False, "error": f"模型适配器注册失败: {err}"}
                self._log_rt("adapter_auto_registered", f"适配器 '{model_id}' 已自动注册")
            else:
                return {"success": False, "error": f"模型适配器 '{model_id}' 未注册且无配置信息可用"}

        if not dataset_ids:
            return {"success": False, "error": "必须指定至少一个检测数据集 (dataset_ids)"}

        current_state = self.get_system_state()
        if current_state == "idle":
            try:
                self._enqueue_in_progress = True
                self._fsm.start_detection()
                self._log_state_transition("idle", "detecting", "start_detection")
                self._notify_state()
            except Exception as e:
                self._enqueue_in_progress = False
                self._log_err("FSMError", f"start_detection 状态转换失败: {e}")
                return {"success": False, "error": "系统状态不允许启动检测"}
        elif current_state != "detecting":
            return {"success": False, "error": f"系统当前状态为'{current_state}'，不允许启动检测"}

        task_group_id = str(uuid.uuid4())
        task_ids: list[str] = []
        try:
            for ds_id in dataset_ids:
                tid = await self._task_queue.enqueue_task({
                    "user_id": str(user_id),
                    "model_id": model_id,
                    "algorithm_type": detection_type,
                    "dataset_id": str(ds_id),
                    "metadata": {
                        "task_group_id": task_group_id,
                        "max_iterations": max_iterations,
                        "jailbreak_dataset_ids": jailbreak_dataset_ids,
                        "force_refresh": force_refresh,
                    },
                })
                task_ids.append(tid)
        finally:
            self._enqueue_in_progress = False

        self._log_op(user_id, "start_detection", {
            "task_group_id": task_group_id, "task_ids": task_ids,
        })
        self._log_rt("detection_queued", f"任务组 {task_group_id} 已入队, 共 {len(task_ids)} 个子任务")

        return {"success": True, "task_group_id": task_group_id, "task_ids": task_ids}

    async def execute_detection_task(self, task_id: str, task_params: dict) -> dict:
        current_status = await self._task_queue.get_task_status(task_id)
        if current_status == TaskStatus.CANCELLED:
            self._log_rt("task_skipped", f"子任务 {task_id} 已取消，跳过执行")
            return {"success": False, "task_id": task_id, "error": "任务已取消"}

        await self._task_queue.update_task_status(task_id, TaskStatus.RUNNING)
        self._log_rt("task_started", f"子任务 {task_id} 开始执行")

        model_id = task_params["model_id"]
        user_id = str(task_params["user_id"])
        detection_type = task_params.get("detection_type", "static")
        max_iterations = task_params.get("max_iterations", 3)
        raw_ds_id = task_params.get("dataset_id")
        task_group_id = task_params.get("task_group_id")
        jailbreak_dataset_ids = task_params.get("jailbreak_dataset_ids")
        force_refresh = task_params.get("force_refresh", False)

        actual_model_name = model_id
        try:
            config_id = int(model_id)
            loaded = await self._config.read_config(config_id)
            if loaded:
                actual_model_name = loaded.get("model") or loaded.get("model_id") or model_id
        except (ValueError, TypeError):
            pass

        def _poc_progress_cb(processed: int, total: int, found: int, score_counts: dict = None, subtype_stats: dict = None) -> None:
            progress = {
                "processed": processed,
                "total": total,
                "found": found,
                "score_counts": score_counts or {},
                "last_update_time": time.monotonic(),
            }
            if subtype_stats is not None:
                progress["subtype_stats"] = subtype_stats
                remaining = [st for st, info in subtype_stats.items() if not info.get("event_set", False)]
                progress["remaining_subtypes"] = remaining
            if not hasattr(_poc_progress_cb, '_started'):
                _poc_progress_cb._started = True
                progress["start_time"] = time.monotonic()
            asyncio.ensure_future(self._task_queue.update_poc_progress(
                task_group_id, progress
            ))

        def _task_progress_cb(task_id: str, processed: int, total: int) -> None:
            asyncio.ensure_future(self._task_queue.update_task_progress(
                task_id, processed, total
            ))

        def _llm_call_cb(request_info: dict, response_info: dict) -> None:
            self._notify_llm_call(request_info, response_info)

        def _dynamic_progress_cb(processed: int, total: int, avg_iterations: float) -> None:
            asyncio.ensure_future(self._task_queue.update_dynamic_progress(
                task_group_id, {"processed": processed, "total": total, "avg_iterations": avg_iterations}
            ))

        cancel_event = asyncio.Event()

        async def _check_cancelled():
            while not cancel_event.is_set():
                await asyncio.sleep(2)
                st = await self._task_queue.get_task_status(task_id)
                if st == TaskStatus.CANCELLED:
                    cancel_event.set()
                    return

        checker = asyncio.create_task(_check_cancelled())

        try:
            dataset_ids = [int(raw_ds_id)] if raw_ds_id is not None else None
            if cancel_event.is_set():
                raise asyncio.CancelledError()
            if detection_type == "static":
                result = await self._detector.run_static_detection(actual_model_name, user_id, dataset_ids, task_group_id=task_group_id, jailbreak_dataset_ids=jailbreak_dataset_ids, poc_progress_callback=_poc_progress_cb, task_progress_callback=_task_progress_cb, force_refresh=force_refresh, llm_callback=_llm_call_cb)
            elif detection_type == "dynamic":
                static_result = await self._detector.run_static_detection(actual_model_name, user_id, dataset_ids, task_group_id=task_group_id, jailbreak_dataset_ids=jailbreak_dataset_ids, poc_progress_callback=_poc_progress_cb, task_progress_callback=_task_progress_cb, force_refresh=force_refresh, llm_callback=_llm_call_cb)
                if static_result["status"] != "completed":
                    result = static_result
                else:
                    dynamic_result = await self._detector.run_dynamic_detection(
                        actual_model_name, user_id, static_result, max_iterations, llm_callback=_llm_call_cb, dynamic_progress_callback=_dynamic_progress_cb
                    )
                    result = {
                        "status": "completed",
                        "static_task_group_id": static_result["task_group_id"],
                        "dynamic_task_group_id": dynamic_result.get("task_group_id"),
                    }
            else:
                static_result = await self._detector.run_static_detection(actual_model_name, user_id, dataset_ids, task_group_id=task_group_id, jailbreak_dataset_ids=jailbreak_dataset_ids, poc_progress_callback=_poc_progress_cb, task_progress_callback=_task_progress_cb, force_refresh=force_refresh, llm_callback=_llm_call_cb)
                if static_result["status"] != "completed":
                    result = static_result
                else:
                    dynamic_result = await self._detector.run_dynamic_detection(
                        actual_model_name, user_id, static_result, max_iterations, llm_callback=_llm_call_cb, dynamic_progress_callback=_dynamic_progress_cb
                    )
                    result = {
                        "status": "completed",
                        "static_task_group_id": static_result["task_group_id"],
                        "dynamic_task_group_id": dynamic_result.get("task_group_id"),
                    }
            current_status = await self._task_queue.get_task_status(task_id)
            if current_status == TaskStatus.CANCELLED:
                self._log_rt("task_cancelled_during_execution", f"子任务 {task_id} 在执行期间被取消")
                return {"success": False, "task_id": task_id, "error": "任务已取消"}
            await self._task_queue.update_task_status(task_id, TaskStatus.COMPLETED)
            self._log_rt("task_completed", f"子任务 {task_id} 执行完成")
            return {"success": True, "task_id": task_id, "result": result}
        except asyncio.CancelledError:
            await self._task_queue.update_task_status(task_id, TaskStatus.CANCELLED)
            self._log_rt("task_cancelled_during_execution", f"子任务 {task_id} 被取消")
            return {"success": False, "task_id": task_id, "error": "任务已取消"}
        except Exception as e:
            await self._task_queue.update_task_status(task_id, TaskStatus.FAILED, str(e))
            self._log_err("DetectionError", f"子任务 {task_id} 异常: {e}")
            return {"success": False, "task_id": task_id, "error": str(e)}
        finally:
            cancel_event.set()
            checker.cancel()
            try:
                await checker
            except asyncio.CancelledError:
                pass
            if task_group_id:
                await self._task_queue.clear_poc_progress(task_group_id)
                await self._task_queue.clear_dynamic_progress(task_group_id)

    async def execute_concurrent_tasks(self, max_concurrency: int = 3) -> dict:
        batch = await self._task_queue.dequeue_tasks(max_concurrency)
        if not batch:
            if self.get_system_state() == "detecting" and not self._enqueue_in_progress:
                try:
                    old_state = self.get_system_state()
                    self._fsm.detection_done()
                    new_state = self.get_system_state()
                    self._log_state_transition(old_state, new_state, "detection_done")
                    self._notify_state()
                except Exception as e:
                    self._log_err("FSMError", f"detection_done 状态转换失败: {e}")
            return {"success": True, "tasks": [], "message": "队列为空"}

        async def _run(task) -> dict:
            params = {
                "model_id": task.model_id,
                "user_id": task.user_id,
                "detection_type": task.algorithm_type,
                "dataset_id": task.dataset_id,
                "max_iterations": task.metadata.get("max_iterations", 3),
                "task_group_id": task.metadata.get("task_group_id"),
                "jailbreak_dataset_ids": task.metadata.get("jailbreak_dataset_ids"),
                "force_refresh": task.metadata.get("force_refresh", False),
            }
            return await self.execute_detection_task(task.task_id, params)

        async with asyncio.TaskGroup() as tg:
            futures = [tg.create_task(_run(task)) for task in batch]

        results = [f.result() for f in futures]

        queue_view = await self._task_queue.get_queue_view()
        has_pending = any(
            t.status in (TaskStatus.PENDING, TaskStatus.RUNNING) for t in queue_view
        )
        if not has_pending and self.get_system_state() == "detecting":
            try:
                old_state = self.get_system_state()
                self._fsm.detection_done()
                new_state = self.get_system_state()
                self._log_state_transition(old_state, new_state, "detection_done")
                self._notify_state()
            except Exception as e:
                self._log_err("FSMError", f"detection_done 状态转换失败: {e}")
        return {"success": True, "tasks": results}

    async def query_detection_progress(self, task_id: Optional[str] = None) -> dict:
        if task_id is not None:
            status = await self._task_queue.get_task_status(task_id)
            if status is None:
                return {"success": False, "error": "任务不存在"}
            return {"success": True, "task_id": task_id, "status": status.value}

        queue_view = await self._task_queue.get_queue_view()

        all_datasets = await self._config.query_datasets()
        dataset_name_map: dict[str, str] = {}
        for ds in all_datasets:
            ds_id = str(ds.get("dataset_id", ""))
            if ds_id:
                dataset_name_map[ds_id] = ds.get("name", ds_id)

        task_group_map: dict[str, list] = {}
        for t in queue_view:
            group_id = t.metadata.get("task_group_id", t.task_id)
            if group_id not in task_group_map:
                task_group_map[group_id] = []
            task_group_map[group_id].append(t)

        existing_group_ids: set[str] | None = None
        terminal_group_ids = {
            gid for gid, tasks in task_group_map.items()
            if all(t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED) for t in tasks)
        }
        if terminal_group_ids:
            try:
                reports = await self._report.list_reports()
                existing_group_ids = {r["task_group_id"] for r in reports}
            except Exception:
                existing_group_ids = None

        orphan_group_ids: set[str] = set()
        if existing_group_ids is not None:
            orphan_group_ids = terminal_group_ids - existing_group_ids

        for orphan_id in orphan_group_ids:
            orphan_tasks = task_group_map.pop(orphan_id, [])
            for t in orphan_tasks:
                try:
                    await self._task_queue.remove_task(t.task_id)
                except Exception:
                    pass
            if orphan_tasks:
                self._log_rt("orphan_cleanup", f"清理孤儿任务组 {orphan_id}, 移除 {len(orphan_tasks)} 个任务")

        groups = []
        config_ids_to_read = []
        for group_id, tasks in task_group_map.items():
            first = tasks[0]
            try:
                config_ids_to_read.append(int(first.model_id))
            except (ValueError, TypeError):
                pass

        configs_map = {}
        if config_ids_to_read:
            configs_map = await self._config.read_configs_batch(config_ids_to_read)

        for group_id, tasks in task_group_map.items():
            first = tasks[0]
            model_name = first.model_id
            try:
                config = configs_map.get(int(first.model_id))
                if config:
                    model_id_content = config.get("model_id") or config.get("model") or first.model_id
                    request_format = config.get("request_format", "")
                    format_labels = {"openai": "OpenAI", "anthropic": "Anthropic", "azure": "Azure"}
                    label = format_labels.get(request_format)
                    model_name = f"{model_id_content} ({label})" if label else model_id_content
            except (ValueError, TypeError):
                pass

            status_counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
            children = []
            for t in tasks:
                status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1
                task_prog = await self._task_queue.get_task_progress(t.task_id)
                child = {
                    "task_id": t.task_id,
                    "status": t.status.value,
                    "dataset_id": t.dataset_id,
                    "dataset_name": dataset_name_map.get(t.dataset_id, t.dataset_id),
                    "error_message": t.error_message if t.status.value == "failed" else "",
                }
                if task_prog:
                    child["progress"] = task_prog
                children.append(child)

            poc_progress = await self._task_queue.get_poc_progress(group_id)
            poc_eta = -1.0
            stage_info = {"stage": "unknown"}
            if poc_progress:
                sc = poc_progress.get("score_counts", {})
                score_parts = []
                for s in range(1, 6):
                    cnt = sc.get(str(s), sc.get(s, 0))
                    if cnt > 0:
                        score_parts.append(f"{s}分{cnt}条")
                found_info = "、".join(score_parts) if score_parts else f"有效 {poc_progress['found']} 条"
                children.insert(0, {
                    "task_id": f"poc_{group_id}",
                    "status": "running",
                    "dataset_id": "poc_selecting",
                    "dataset_name": f"构建PoC池 ({poc_progress['processed']}/{poc_progress['total']}，{found_info})",
                    "error_message": "",
                })
                status_counts["running"] += 1
                subtype_stats = poc_progress.get("subtype_stats", {})
                remaining_subtypes = poc_progress.get("remaining_subtypes", [])
                start_time = poc_progress.get("start_time")
                last_update_time = poc_progress.get("last_update_time")
                if not remaining_subtypes:
                    poc_eta = 0.0
                    stage_info = {"stage": "poc_selecting", "remaining_subtypes": [], "estimated_needed": poc_progress["processed"]}
                elif start_time and last_update_time and subtype_stats:
                    elapsed = last_update_time - start_time
                    processed = poc_progress["processed"]
                    if elapsed > 0 and processed > 0:
                        overall_speed = processed / elapsed
                        subtype_etas = []
                        for st in remaining_subtypes:
                            st_info = subtype_stats.get(st, {})
                            current = st_info.get("current", 0)
                            target = st_info.get("target", 3)
                            remaining = target - current
                            if remaining > 0 and current > 0:
                                st_elapsed = elapsed
                                st_speed = current / st_elapsed if st_elapsed > 0 else 0
                                if st_speed < 0.01:
                                    subtype_etas.append((st, float('inf')))
                                else:
                                    subtype_etas.append((st, remaining / st_speed))
                            elif remaining > 0:
                                subtype_etas.append((st, float('inf')))
                        if subtype_etas:
                            max_eta_st, max_eta_val = max(subtype_etas, key=lambda x: x[1])
                            poc_eta = max_eta_val if max_eta_val != float('inf') else -1.0
                        else:
                            poc_eta = 0.0
                        estimated_needed = poc_progress["processed"] + (poc_eta * overall_speed if overall_speed > 0 and poc_eta > 0 else 0)
                        stage_info = {
                            "stage": "poc_selecting",
                            "remaining_subtypes": remaining_subtypes,
                            "estimated_needed": int(estimated_needed),
                        }
                        if poc_eta < 0:
                            slow_subtypes = [st for st, v in subtype_etas if v == float('inf')]
                            if slow_subtypes:
                                stage_info["slow_subtypes"] = slow_subtypes
                    else:
                        stage_info = {"stage": "poc_selecting", "remaining_subtypes": remaining_subtypes}
                else:
                    stage_info = {"stage": "poc_selecting", "remaining_subtypes": remaining_subtypes}

            total = len(tasks)
            if status_counts["failed"] > 0:
                group_status = "failed"
            elif status_counts["running"] > 0:
                group_status = "running"
            elif status_counts["pending"] > 0:
                group_status = "pending"
            elif status_counts["cancelled"] == total:
                group_status = "cancelled"
            else:
                group_status = "completed"

            eta_seconds = -1.0
            if poc_eta >= 0:
                eta_seconds = poc_eta
                stage_info = stage_info
            elif poc_progress is None and group_status in ("running", "pending"):
                task_etas = []
                for child in children:
                    if child.get("status") == "running" and "progress" in child:
                        prog = child["progress"]
                        recent_speeds = prog.get("recent_speeds", [])
                        processed = prog.get("processed", 0)
                        task_total = prog.get("total", 0)
                        if recent_speeds and processed < task_total:
                            avg_speed = sum(recent_speeds) / len(recent_speeds)
                            if avg_speed > 0:
                                task_etas.append((task_total - processed) / avg_speed)
                if task_etas:
                    eta_seconds = max(task_etas)
                    stage_info = {"stage": "static_detecting", "tasks_remaining": sum(1 for c in children if c.get("status") in ("pending", "running"))}
                else:
                    stage_info = {"stage": "static_detecting", "tasks_remaining": sum(1 for c in children if c.get("status") in ("pending", "running"))}

            dynamic_prog = await self._task_queue.get_dynamic_progress(group_id)
            if dynamic_prog and group_status == "running":
                dyn_processed = dynamic_prog.get("processed", 0)
                dyn_total = dynamic_prog.get("total", 0)
                dyn_avg_iter = dynamic_prog.get("avg_iterations", 0.0)
                dyn_speeds = dynamic_prog.get("recent_speeds", [])
                if dyn_speeds and dyn_processed < dyn_total:
                    avg_speed = sum(dyn_speeds) / len(dyn_speeds)
                    if avg_speed > 0:
                        dyn_eta = (dyn_total - dyn_processed) / avg_speed
                        if dyn_eta > eta_seconds or eta_seconds < 0:
                            eta_seconds = dyn_eta
                        stage_info = {
                            "stage": "dynamic_detecting",
                            "avg_iterations": round(dyn_avg_iter, 2),
                            "samples_remaining": dyn_total - dyn_processed,
                        }
                    else:
                        stage_info = {"stage": "dynamic_detecting", "avg_iterations": round(dyn_avg_iter, 2), "samples_remaining": dyn_total - dyn_processed}
                elif dyn_processed >= dyn_total:
                    eta_seconds = 0.0
                    stage_info = {"stage": "dynamic_detecting", "avg_iterations": round(dyn_avg_iter, 2), "samples_remaining": 0}

            if group_status == "completed":
                eta_seconds = 0.0
                stage_info = {"stage": "completed"}

            groups.append({
                "task_group_id": group_id,
                "model_id": first.model_id,
                "model_name": model_name,
                "status": group_status,
                "progress": {**status_counts, "total": total},
                "children": children,
                "eta_seconds": eta_seconds,
                "stage_info": stage_info,
            })

        return {"success": True, "groups": [g for g in groups if g["status"] != "cancelled"]}

    async def cancel_task(self, task_id: str) -> dict:
        ok = await self._task_queue.cancel_task(task_id)
        if not ok:
            return {"success": False, "error": "任务不存在或已处于终态"}
        self._log_rt("task_cancelled", f"任务 {task_id} 已取消")

        remaining = await self._task_queue.get_queue_view()
        has_active = any(t.status in (TaskStatus.PENDING, TaskStatus.RUNNING) for t in remaining)
        if not has_active and self.get_system_state() == "detecting":
            try:
                old_state = self.get_system_state()
                self._fsm.detection_done()
                new_state = self.get_system_state()
                self._log_state_transition(old_state, new_state, "cancel_task")
                self._notify_state()
            except Exception as e:
                self._log_err("FSMError", f"取消后状态转换失败: {e}")

        return {"success": True}

    async def cancel_task_group(self, task_group_id: str) -> dict:
        queue_view = await self._task_queue.get_queue_view()
        group_tasks = [t for t in queue_view if t.metadata.get("task_group_id") == task_group_id]

        cancelled_count = 0
        task_ids_to_remove = []
        for t in group_tasks:
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                ok = await self._task_queue.cancel_task(t.task_id)
                if ok:
                    cancelled_count += 1
            else:
                task_ids_to_remove.append(t.task_id)

        for tid in task_ids_to_remove:
            await self._task_queue.remove_task(tid)

        try:
            await self._report.delete_report(task_group_id=task_group_id)
        except Exception:
            pass

        remaining = await self._task_queue.get_queue_view()
        has_active = any(t.status in (TaskStatus.PENDING, TaskStatus.RUNNING) for t in remaining)
        if not has_active and self.get_system_state() == "detecting":
            try:
                old_state = self.get_system_state()
                self._fsm.detection_done()
                new_state = self.get_system_state()
                self._log_state_transition(old_state, new_state, "cancel_task_group")
                self._notify_state()
            except Exception as e:
                self._log_err("FSMError", f"取消后状态转换失败: {e}")

        self._log_rt("task_group_cancelled", f"任务组 {task_group_id} 已取消, 共取消 {cancelled_count} 个子任务, 已从队列移除 {len(group_tasks)} 个任务")
        return {"success": True, "cancelled_count": cancelled_count, "removed_count": len(group_tasks)}

    # ── 报告管理调度 (职责 5-8) ──

    async def generate_report(self, task_group_id: str, detection_type: str, *, user_id: int | None = None) -> dict:
        try:
            old_state = self.get_system_state()
            self._fsm.start_report()
            new_state = self.get_system_state()
            self._log_state_transition(old_state, new_state, "start_report")
            self._notify_state()
        except Exception:
            return {"success": False, "error": "系统状态不允许生成报告"}

        try:
            if detection_type == "static":
                report = await self._report.generate_static_report(task_group_id)
            else:
                report = await self._report.generate_dynamic_report(task_group_id)
            old_state = self.get_system_state()
            self._fsm.report_done()
            new_state = self.get_system_state()
            self._log_state_transition(old_state, new_state, "report_done")
            self._notify_state()
            self._log_rt("report_generated", f"报告已生成: {task_group_id}")
            return {"success": True, "report": report}
        except Exception as e:
            self._handle_error(e, "ReportError")
            return {"success": False, "error": str(e)}

    async def view_report(self, task_group_id: str, *, user_id: int | None = None) -> dict:
        report = await self._report.view_report(task_group_id, user_id=user_id)
        if isinstance(report, dict) and "error" in report:
            return {"success": False, "error": report["error"]}
        return {"success": True, "report": report}

    async def list_reports(self, filters: Optional[dict] = None) -> list:
        f = filters or {}
        return await self._report.list_reports(
            user_id=f.get("user_id"), model_id=f.get("model_id"),
        )

    async def delete_report(
        self, target_id: str, caller_user_id: int, granularity: str = "task_group"
    ) -> dict:
        kwargs: dict = {}
        if granularity == "task_group":
            kwargs["task_group_id"] = target_id
        elif granularity == "task":
            kwargs["task_id"] = target_id
        elif granularity == "report":
            kwargs["report_id"] = target_id
        elif granularity == "result_data":
            kwargs["result_data_id"] = target_id

        ok, msg = await self._report.delete_report(user_id=caller_user_id, **kwargs)
        self._log_op(caller_user_id, "delete_report", {"target_id": target_id, "granularity": granularity})

        if ok:
            try:
                await self._cleanup_task_queue_after_report_delete(target_id, granularity)
            except Exception as e:
                self._log_err("queue_cleanup", f"删除报告后清理任务队列失败: {e}")

        return {"success": ok, "message": msg}

    async def _cleanup_task_queue_after_report_delete(self, target_id: str, granularity: str) -> None:
        queue_view = await self._task_queue.get_queue_view()

        if granularity == "task_group":
            group_tasks = [t for t in queue_view if t.metadata.get("task_group_id") == target_id]
            for t in group_tasks:
                if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    await self._task_queue.cancel_task(t.task_id)
                await self._task_queue.remove_task(t.task_id)
            if group_tasks:
                self._log_rt("queue_cleaned_after_report_delete", f"删除报告后清理任务队列: 任务组 {target_id}, 移除 {len(group_tasks)} 个任务")
        elif granularity == "task":
            task = next((t for t in queue_view if t.task_id == target_id), None)
            if task:
                if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    await self._task_queue.cancel_task(task.task_id)
                await self._task_queue.remove_task(task.task_id)
                self._log_rt("queue_cleaned_after_report_delete", f"删除报告后清理任务队列: 任务 {target_id}")

    async def export_report(self, task_group_id: str, target_format: str, *, user_id: int | None = None, task_id: str | None = None) -> dict:
        filename, content = await self._report.export_report(task_group_id, target_format, user_id=user_id, task_id=task_id)
        self._log_rt("report_exported", f"报告 {task_group_id} 已导出为 {target_format}")
        return {"success": True, "filename": filename, "content": content}

    async def prepare_visualization_data(self, task_group_id: str, *, user_id: int | None = None) -> dict:
        data = await self._report.prepare_visualization_data(task_group_id, user_id=user_id)
        if isinstance(data, dict) and "error" in data and "risk_distribution" not in data:
            return {"success": False, "error": data["error"]}
        return {"success": True, "data": data}

    async def prepare_task_visualization_data(self, task_id: str, *, user_id: int | None = None) -> dict:
        data = await self._report.prepare_task_visualization_data(task_id, user_id=user_id)
        if isinstance(data, dict) and "error" in data and "risk_distribution" not in data:
            return {"success": False, "error": data["error"]}
        return {"success": True, "data": data}

    async def query_compliance_statistics(self) -> dict:
        stats = await self._report.get_compliance_statistics()
        return {"success": True, **stats}

    # ── 系统状态与日志 (职责 9-12) ──

    def get_system_state(self) -> str:
        return next(iter(self._fsm.configuration)).id

    def subscribe_state_changes(self, callback: Callable[[str], None]) -> None:
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def unsubscribe_state_changes(self, callback: Callable[[str], None]) -> None:
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def subscribe_errors(self, callback: Callable[[str, str], None]) -> None:
        if callback not in self._error_callbacks:
            self._error_callbacks.append(callback)

    def unsubscribe_errors(self, callback: Callable[[str, str], None]) -> None:
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    def subscribe_logs(self, callback: Callable[[dict], None]) -> None:
        if callback not in self._log_callbacks:
            self._log_callbacks.append(callback)

    def unsubscribe_logs(self, callback: Callable[[dict], None]) -> None:
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)

    def subscribe_llm_calls(self, callback: Callable[[dict, dict], None]) -> None:
        """订阅 LLM 调用事件，callback 接收 (request_info, response_info)"""
        if callback not in self._llm_call_callbacks:
            self._llm_call_callbacks.append(callback)

    def unsubscribe_llm_calls(self, callback: Callable[[dict, dict], None]) -> None:
        """取消 LLM 调用订阅"""
        if callback in self._llm_call_callbacks:
            self._llm_call_callbacks.remove(callback)

    def _notify_llm_call(self, request_info: dict, response_info: dict) -> None:
        for cb in list(self._llm_call_callbacks):
            try:
                cb(request_info, response_info)
            except Exception:
                pass

    def _notify_state(self) -> None:
        state = self.get_system_state()
        for cb in list(self._state_callbacks):
            try:
                cb(state)
            except Exception as e:
                self._logger.log_error("StateScheduler", "CallbackError", f"状态回调异常: {e}")

    def _notify_error(self, err_type: str, desc: str) -> None:
        for cb in list(self._error_callbacks):
            try:
                cb(err_type, desc)
            except Exception as e:
                self._logger.log_error("StateScheduler", "CallbackError", f"错误回调异常: {e}")

    def _on_new_log(self, log_data: dict) -> None:
        for cb in list(self._log_callbacks):
            try:
                cb(log_data)
            except Exception:
                pass


    async def query_logs(self, filters: Optional[dict] = None) -> dict:
        f = filters or {}
        category = None
        cat_str = f.get("category")
        if cat_str:
            category = LogCategory(cat_str)
        level = None
        level_str = f.get("level")
        if level_str:
            from sdpj.core.event_logger_interface import LogLevel
            level = LogLevel(level_str.lower())
        entries, total = await self._logger.query_logs(
            category=category,
            level=level,
            time_start=f.get("time_start"),
            time_end=f.get("time_end"),
            source_module=f.get("source_module"),
            user_id=f.get("user_id"),
            user_ids=f.get("user_ids"),
            page=f.get("page"),
            page_size=f.get("page_size"),
        )
        logs = [
            {
                "log_id": e.log_id,
                "category": e.category.value,
                "level": e.level.value,
                "timestamp": e.timestamp,
                "source_module": e.source_module,
                "user_id": e.user_id,
                "event_type": e.event_type,
                "description": e.description,
                "context": e.context,
            }
            for e in entries
        ]
        return {"logs": logs, "total": total}

    def _handle_error(self, exc: Exception, err_type: str) -> None:
        self._log_err(err_type, str(exc))
        self._notify_error(err_type, str(exc))
        try:
            old_state = self.get_system_state()
            self._fsm.to_error()
            new_state = self.get_system_state()
            self._log_state_transition(old_state, new_state, "to_error")
            self._notify_state()
        except Exception:
            pass
        try:
            old_state = self.get_system_state()
            self._fsm.recover()
            new_state = self.get_system_state()
            self._log_state_transition(old_state, new_state, "recover")
            self._notify_state()
        except Exception:
            pass

    # ── 用户账号调度 (职责 13-14) ──

    async def schedule_user_auth(
        self, username: str, password: str, action: str
    ) -> dict:
        pwd = password

        if action == "register":
            ok, user_id, msg = await self._account.register(username, pwd)
            if ok:
                self._log_op(user_id or 0, "register", {"username": username})
            return {"success": ok, "user_id": user_id, "message": msg}

        if action == "login":
            ok, user_id, error_msg = await self._account.login(username, pwd)
            if ok:
                self._log_op(user_id or 0, "login", {"username": username})
                return {"success": True, "user_id": user_id}
            return {"success": False, "message": error_msg}

        return {"success": False, "error": f"未知操作: {action}"}

    async def list_all_users(self) -> list[dict]:
        """获取所有用户列表"""
        users = await self._account.list_all_users()
        return [
            {
                "user_id": u.get("user_id"),
                "username": u.get("username"),
                "created_at": u.get("created_at", "-")
            }
            for u in users
        ]

    async def schedule_account_operation(self, operation: str, params: dict) -> dict:
        dispatch = {
            "change_password": self._op_change_password,
            "switch_account": self._op_switch_account,
            "logout": self._op_logout,
            "unregister": self._op_unregister,
            "get_profile": self._op_get_profile,
            "update_profile": self._op_update_profile,
            "list_resources": self._op_list_resources,
            "admin_delete_user": self._op_admin_delete_user,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return {"success": False, "error": f"未知账号操作: {operation}"}
        return await handler(params)

    async def _op_change_password(self, p: dict) -> dict:
        user_id = p.get("user_id")
        if user_id is None:
            return {"success": False, "error": "缺少 user_id"}
        old_pwd = p["old_password"]
        new_pwd = p["new_password"]
        ok, msg = await self._account.change_password_for_user(int(user_id), old_pwd, new_pwd)
        self._log_op(user_id, "change_password", {})
        return {"success": ok, "message": msg}

    async def _op_switch_account(self, p: dict) -> dict:
        ok, uid = await self._account.switch_account(p["username"], p["password"])
        if ok:
            self._log_op(uid or 0, "switch_account", {"username": p["username"]})
        return {"success": ok, "user_id": uid}

    async def _op_logout(self, _p: dict) -> dict:
        ok = self._account.logout()
        self._log_op(0, "logout", {})
        return {"success": ok}

    async def _op_unregister(self, p: dict) -> dict:
        ok, msg = await self._account.unregister(p["user_id"])
        self._log_op(p["user_id"], "unregister", {})
        return {"success": ok, "message": msg}

    async def _op_get_profile(self, p: dict) -> dict:
        user_id = p.get("user_id")
        if user_id is None:
            return {"success": False, "error": "缺少 user_id"}
        profile = await self._account.get_profile_for_user(int(user_id))
        return {"success": profile is not None, "profile": profile}

    async def _op_update_profile(self, p: dict) -> dict:
        user_id = p.get("user_id")
        username = p.get("username")
        if not user_id or not username:
            return {"success": False, "error": "user_id 和 username 不能为空"}
        ok = await self._account.update_username_for_user(int(user_id), username)
        return {"success": ok}

    async def _op_list_resources(self, p: dict) -> dict:
        user_id = p.get("user_id")
        if user_id is None:
            return {"success": False, "error": "缺少 user_id"}
        resources = await self._account.list_resources_for_user(int(user_id))
        shared_resources = await self._account.list_shared_resources_for_user(int(user_id))
        datasets = await self._config.query_datasets()
        dataset_map = {ds.get("resource_id"): ds for ds in datasets if ds.get("resource_id")}
        for r in resources + shared_resources:
            if r.get("resource_type") == "private_config":
                content = await self._config.read_config(r["resource_id"])
                if content:
                    r["model_id"] = content.get("model_id") or content.get("model")
            elif r.get("resource_type") == "private_dataset":
                ds = dataset_map.get(r["resource_id"])
                if ds:
                    r["dataset_name"] = ds.get("name")
        return {"success": True, "resources": resources, "shared_resources": shared_resources}

    async def _op_admin_delete_user(self, p: dict) -> dict:
        user_id = p.get("user_id")
        if user_id is None:
            return {"success": False, "error": "缺少 user_id"}
        ok, msg = await self._account.unregister(int(user_id))
        self._log_op(int(user_id), "admin_delete_user", {})
        return {"success": ok, "message": msg}

    # ── 权限授权调度 (职责 15-16) ──

    async def schedule_dac_operation(self, operation: str, params: dict) -> dict:
        caller = params["caller_user_id"]

        if operation == "grant":
            ok, msg = await self._dac.grant_access(
                params["resource_id"], params["target_username"], caller,
            )
            self._log_op(caller, "grant_access", params)
            return {"success": ok, "message": msg}

        if operation == "revoke":
            ok, msg = await self._dac.revoke_access(params["acl_id"], caller)
            self._log_op(caller, "revoke_access", params)
            return {"success": ok, "message": msg}

        if operation == "list":
            ok, acl_list = await self._dac.get_access_list(params["resource_id"], caller)
            return {"success": ok, "acl_list": acl_list}

        return {"success": False, "error": f"未知权限操作: {operation}"}

    async def check_resource_access(self, resource_id: int, user_id: int) -> bool:
        return await self._dac.check_access(resource_id, user_id)

    # ── 私有资源调度 (职责 17, 17-1, 18) ──

    async def schedule_config_operation(self, operation: str, params: dict) -> dict:
        user_id: int = params.get("user_id", 0)
        is_write = operation in {"create", "update", "delete", "import"}

        if is_write:
            try:
                old_state = self.get_system_state()
                self._fsm.start_configuring()
                new_state = self.get_system_state()
                self._log_state_transition(old_state, new_state, "start_configuring")
                self._notify_state()
            except Exception:
                return {"success": False, "error": "系统状态不允许修改配置"}

        try:
            if operation == "create":
                config_content = params["config_content"]
                ok, cid = await self._config.create_config(user_id, config_content)
                self._log_op(user_id, "create_config", {"config_id": cid})
                return {"success": ok, "config_id": cid}

            if operation in ("read", "update", "delete", "export"):
                config_id: int = params["config_id"]
                has_access = await self._dac.check_access(config_id, user_id)
                if not has_access:
                    return {"success": False, "error": "无访问权限"}

            if operation == "verify":
                config_id: int = params["config_id"]
                config = await self._config.read_config(config_id)
                if config is None:
                    return {"success": False, "error": "配置不存在"}
                has_access = await self._dac.check_access(config_id, user_id)
                if not has_access:
                    return {"success": False, "error": "无访问权限"}
                return await self._verify_config_availability(config_id, user_id, config)

            if operation == "read":
                data = await self._config.read_config(params["config_id"])
                return {"success": data is not None, "config": data}

            if operation == "update":
                config_content = params["config_content"]
                ok, msg = await self._config.update_config(params["config_id"], config_content)
                self._log_op(user_id, "update_config", {"config_id": params["config_id"]})
                return {"success": ok, "message": msg}

            if operation == "delete":
                ok = await self._config.delete_config(params["config_id"])
                self._log_op(user_id, "delete_config", {"config_id": params["config_id"]})
                return {"success": ok}

            if operation == "list":
                configs = await self._config.list_configs(user_id)
                return {"success": True, "configs": configs}

            if operation == "export":
                content = await self._config.export_config(params["config_id"], params.get("format", "json"))
                self._log_op(user_id, "export_config", {"config_id": params["config_id"]})
                return {"success": True, "content": content}

            if operation == "import":
                file_content = params["file_content"]
                ok, cid = await self._config.import_config(file_content, user_id)
                self._log_op(user_id, "import_config", {"config_id": cid})
                return {"success": ok, "config_id": cid}

            return {"success": False, "error": f"未知配置操作: {operation}"}
        finally:
            if is_write:
                try:
                    old_state = self.get_system_state()
                    self._fsm.configuring_done()
                    new_state = self.get_system_state()
                    self._log_state_transition(old_state, new_state, "configuring_done")
                    self._notify_state()
                except Exception:
                    pass

    async def _verify_config_availability(self, config_id: int, user_id: int, config: dict) -> dict:
        import asyncio
        import uuid
        import time

        adapter_content = json.dumps(config)
        temp_model_id = f"__verify_{uuid.uuid4().hex[:8]}"

        try:
            ok, _, err = await self._registry.register_private_model(adapter_content, temp_model_id)
            if not ok:
                return {"success": False, "result": {"status": "config_error", "error": f"适配器注册失败: {err}"}}

            _, instance = await self._registry.is_model_available(temp_model_id)
            if instance is None:
                return {"success": False, "result": {"status": "config_error", "error": "适配器实例创建失败"}}

            req = self._detector._llm.assemble_request("", "Hello, respond with exactly: OK")
            start = time.monotonic()
            try:
                resp = await asyncio.wait_for(
                    self._detector._llm.invoke_llm(instance, req),
                    timeout=30.0,
                )
                latency_ms = int((time.monotonic() - start) * 1000)
                content = resp.get("content", "")
                model = resp.get("model", "")
                self._log_op(user_id, "verify_config", {"config_id": config_id, "status": "ok"})
                return {
                    "success": True,
                    "result": {
                        "status": "ok",
                        "model": model,
                        "latency_ms": latency_ms,
                        "response_preview": content[:200],
                    },
                }
            except asyncio.TimeoutError:
                latency_ms = int((time.monotonic() - start) * 1000)
                self._log_op(user_id, "verify_config", {"config_id": config_id, "status": "timeout"})
                return {
                    "success": False,
                    "result": {"status": "timeout", "error": f"验证超时(30s)", "latency_ms": latency_ms},
                }
            except Exception as e:
                latency_ms = int((time.monotonic() - start) * 1000)
                err_msg = str(e)
                status = "unknown_error"
                if "401" in err_msg or "auth" in err_msg.lower() or "api_key" in err_msg.lower() or "Unauthorized" in err_msg:
                    status = "auth_failed"
                elif "404" in err_msg:
                    status = "format_mismatch"
                elif "connect" in err_msg.lower() or "unreachable" in err_msg.lower() or "refused" in err_msg.lower():
                    status = "unreachable"
                self._log_op(user_id, "verify_config", {"config_id": config_id, "status": status})
                return {
                    "success": False,
                    "result": {"status": status, "error": err_msg, "latency_ms": latency_ms},
                }
        finally:
            try:
                _, inst = await self._registry.is_model_available(temp_model_id)
                if inst and hasattr(inst, 'adapter') and inst.adapter and hasattr(inst.adapter, 'close'):
                    await inst.adapter.close()
            except Exception:
                pass
            try:
                await self._registry.unregister_private_model(temp_model_id)
            except Exception:
                pass

    async def query_available_datasets(self, user_id: int) -> list:
        datasets = await self._config.query_datasets()

        private_datasets = [ds for ds in datasets if ds.get("resource_id") is not None]
        if not private_datasets:
            if user_id > 0:
                self._log_op(user_id, "query_datasets", {})
            return datasets

        resource_ids = [ds["resource_id"] for ds in private_datasets]
        accessible_ids = await self._dac.batch_check_accessible_resource_ids(user_id, resource_ids)

        filtered = []
        for ds in datasets:
            resource_id = ds.get("resource_id")
            if resource_id is None:
                filtered.append(ds)
            elif resource_id in accessible_ids:
                filtered.append(ds)

        if user_id > 0:
            self._log_op(user_id, "query_datasets", {})
        return filtered

    async def query_dataset_detail(self, dataset_id: int, user_id: int | None = None) -> dict | None:
        """查询数据集详情"""
        datasets = await self._config.query_datasets()
        for ds in datasets:
            if ds.get("dataset_id") == dataset_id:
                resource_id = ds.get("resource_id")
                if resource_id is not None and user_id is not None:
                    has_access = await self._dac.check_access(resource_id, user_id)
                    if not has_access:
                        return None
                return ds
        return None

    async def delete_user_dataset(self, dataset_id: int, user_id: int) -> dict:
        """删除用户数据集（仅允许删除有 resource_id 的用户私有数据集）"""
        dataset = await self.query_dataset_detail(dataset_id)
        if not dataset:
            return {"success": False, "error": "数据集不存在"}

        resource_id = dataset.get("resource_id")
        if resource_id is None:
            return {"success": False, "error": "内置数据集不允许删除"}

        has_access = await self._dac.check_access(resource_id, user_id)
        if not has_access:
            return {"success": False, "error": "无访问权限"}

        ok = await self._config.remove_dataset(dataset_id, resource_id)
        if ok:
            self._log_op(user_id, "delete_dataset", {"dataset_id": dataset_id})
        return {"success": ok}

    async def export_dataset_file(self, dataset_id: int, user_id: int | None = None) -> dict | None:
        """导出数据集文件"""
        import json
        import os
        from pathlib import Path

        datasets = await self._config.query_datasets()
        dataset = None
        for ds in datasets:
            if ds.get("dataset_id") == dataset_id:
                dataset = ds
                break

        if not dataset:
            return None

        resource_id = dataset.get("resource_id")
        if resource_id is not None and user_id is not None:
            has_access = await self._dac.check_access(resource_id, user_id)
            if not has_access:
                return {"error": "无访问权限"}

        dataset_name = dataset.get("name", "")

        base_path = Path(os.getcwd()) / "sdpj" / "infrastructure" / "database" / "sample_db"

        if resource_id is not None:
            profile = await self._account.get_profile_for_user(user_id) if user_id else None
            username = profile["username"] if profile else str(user_id)
            if dataset_name.startswith("user_datasets/"):
                file_path = base_path / dataset_name
            else:
                file_path = base_path / "user_datasets" / username / f"{dataset_name}.jsonl"
        else:
            file_path = base_path / f"{dataset_name}.jsonl"

        file_content = None
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except Exception as e:
                self._log_rt("export_dataset_error", f"读取文件失败: {file_path}, 错误: {e}")
                file_content = json.dumps(dataset, ensure_ascii=False, indent=2)
        else:
            self._log_rt("export_dataset_fallback", f"未找到数据集文件: {file_path}")
            file_content = json.dumps(dataset, ensure_ascii=False, indent=2)

        filename = Path(dataset_name).name + '.jsonl'

        return {
            'content': file_content,
            'filename': filename
        }

    async def import_dataset_file(self, user_id: int, filename: str, content: bytes) -> dict:
        """导入数据集文件"""
        import json
        from pathlib import Path

        try:
            # 解码文件内容
            text_content = content.decode('utf-8')

            # 验证文件格式
            if filename.endswith('.jsonl'):
                # JSONL 格式：每行一个 JSON 对象
                lines = text_content.strip().split('\n')
                sample_count = 0
                for line in lines:
                    if line.strip():
                        json.loads(line)  # 验证 JSON 格式
                        sample_count += 1
            elif filename.endswith('.json'):
                # JSON 格式：数组或对象
                data = json.loads(text_content)
                if isinstance(data, list):
                    sample_count = len(data)
                else:
                    sample_count = 1
            elif filename.endswith('.csv'):
                # CSV 格式
                lines = text_content.strip().split('\n')
                sample_count = max(0, len(lines) - 1)  # 减去表头
            else:
                return {"success": False, "error": "不支持的文件格式，仅支持 .json, .jsonl, .csv"}

            # 查询用户名作为目录名
            profile = await self._account.get_profile_for_user(user_id)
            username = profile["username"] if profile else str(user_id)

            # 保存文件到用户数据集目录
            base_path = Path("sdpj/infrastructure/database/sample_db/user_datasets") / username
            base_path.mkdir(parents=True, exist_ok=True)

            # 处理文件名（去除已有的 user_datasets_ 前缀避免重复）
            safe_filename = filename.replace(' ', '_')
            use_direct_name = False
            if safe_filename.startswith('user_datasets_'):
                safe_filename = safe_filename[len('user_datasets_'):]
                use_direct_name = True
            file_path = base_path / safe_filename

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            # 添加到数据库
            if use_direct_name:
                dataset_name = Path(safe_filename).stem
            else:
                dataset_name = f"user_datasets/{username}/{Path(safe_filename).stem}"
            dataset_id, resource_id = await self._config.add_custom_dataset(
                user_id=user_id,
                name=dataset_name,
                sample_count=sample_count,
                file_path=str(file_path)
            )

            self._log_op(user_id, "import_dataset", {"filename": filename, "dataset_id": dataset_id})

            return {"success": True, "dataset_id": dataset_id}

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"文件格式错误: {str(e)}"}
        except Exception as e:
            self._log_rt("import_dataset_error", f"导入失败: {e}")
            return {"success": False, "error": str(e)}

    async def schedule_private_resource_operation(
        self, operation: str, params: dict
    ) -> dict:
        try:
            old_state = self.get_system_state()
            self._fsm.start_configuring()
            new_state = self.get_system_state()
            self._log_state_transition(old_state, new_state, "start_configuring")
            self._notify_state()
        except Exception:
            return {"success": False, "error": "系统状态不允许修改配置"}

        user_id: int = params.get("user_id", 0)
        try:
            if operation == "upload_adapter":
                adapter_content = params["adapter_content"]
                ok, msg, rid = await self._config.upload_adapter(
                    adapter_content, params["model_id"], user_id,
                )
                self._log_op(user_id, "upload_adapter", {"model_id": params["model_id"]})
                return {"success": ok, "message": msg, "resource_id": rid}

            if operation == "remove_adapter":
                resource_id = params.get("resource_id")
                if resource_id is None:
                    return {"success": False, "error": "缺少 resource_id"}
                has_access = await self._dac.check_access(resource_id, user_id)
                if not has_access:
                    return {"success": False, "error": "无访问权限"}
                ok, msg = await self._config.remove_adapter(params["model_id"], resource_id)
                self._log_op(user_id, "remove_adapter", {"model_id": params["model_id"]})
                return {"success": ok, "message": msg}

            if operation == "upload_dataset":
                ok, info = await self._config.upload_dataset(
                    params["name"], params["risk_type"], params["samples"], user_id,
                )
                self._log_op(user_id, "upload_dataset", {"name": params["name"]})
                return {"success": ok, "info": info}

            if operation == "remove_dataset":
                resource_id = params.get("resource_id")
                if resource_id is not None:
                    has_access = await self._dac.check_access(resource_id, user_id)
                    if not has_access:
                        return {"success": False, "error": "无访问权限"}
                ok = await self._config.remove_dataset(params["dataset_id"], resource_id)
                self._log_op(user_id, "remove_dataset", {"dataset_id": params["dataset_id"]})
                return {"success": ok}

            return {"success": False, "error": f"未知私有资源操作: {operation}"}
        finally:
            try:
                old_state = self.get_system_state()
                self._fsm.configuring_done()
                new_state = self.get_system_state()
                self._log_state_transition(old_state, new_state, "configuring_done")
                self._notify_state()
            except Exception:
                pass
