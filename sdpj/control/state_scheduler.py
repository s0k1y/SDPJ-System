"""StateScheduler 系统状态管理及调度控制

依赖模块: AccountManager, DACManager, PrivateConfigManager,
          ReportManager, SDPJDetector, EventLogger, TaskQueueManager, SecureCommManager
被依赖模块: CLI, WebUI
"""
import asyncio
import uuid
import base64
from typing import Callable, Optional

from sdpj.core.account_manager_interface import AccountManagerInterface
from sdpj.core.dac_manager_interface import DACManagerInterface
from sdpj.core.private_config_manager_interface import PrivateConfigManagerInterface
from sdpj.core.report_manager_interface import ReportManagerInterface
from sdpj.core.sdpj_detector_interface import SDPJDetectorInterface
from sdpj.core.event_logger_interface import EventLoggerInterface, LogCategory
from sdpj.core.task_queue_manager_interface import TaskQueueManagerInterface, TaskStatus
from sdpj.core.secure_comm_manager_interface import SecureCommManagerInterface
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
        secure_comm_manager: SecureCommManagerInterface,
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
        self._secure_comm = secure_comm_manager
        self._registry = llm_registry
        self._db_initializer = db_initializer
        self._state_callbacks: list = []
        self._error_callbacks: list = []

    # ── 内部日志辅助 ──

    async def startup(self) -> None:
        if self._db_initializer is not None:
            await self._db_initializer()
        await self._registry.initialize()

    async def shutdown(self) -> None:
        await self._registry.shutdown()

    def _log_op(self, user_id: int, op: str, ctx: dict) -> None:
        self._logger.log_operation(str(user_id), op, ctx)

    def _log_rt(self, event: str, desc: str) -> None:
        self._logger.log_runtime("StateScheduler", event, desc)

    def _log_err(self, err_type: str, desc: str) -> None:
        self._logger.log_error("StateScheduler", err_type, desc)

    # ── 检测调度 (职责 1-4) ──

    async def start_detection(self, user_id: int, config_data: dict) -> dict:
        model_id: str = config_data["model_id"]
        detection_type: str = config_data.get("detection_type", "static")
        dataset_ids: list = config_data.get("dataset_ids", [])
        max_iterations: int = config_data.get("max_iterations", 3)
        config_id: int | None = config_data.get("config_id")

        if config_id is not None:
            loaded = await self._config.read_config(config_id)
            if loaded:
                dataset_ids = loaded.get("dataset_ids", dataset_ids)
                model_id = loaded.get("model_id", model_id)

        try:
            self._fsm.start_detection()
            self._notify_state()
        except Exception:
            return {"success": False, "error": "系统状态不允许启动检测"}

        task_group_id = str(uuid.uuid4())
        task_ids: list[str] = []
        for ds_id in dataset_ids:
            tid = await self._task_queue.enqueue_task({
                "user_id": str(user_id),
                "model_id": model_id,
                "algorithm_type": detection_type,
                "dataset_id": str(ds_id),
                "metadata": {
                    "task_group_id": task_group_id,
                    "max_iterations": max_iterations,
                },
            })
            task_ids.append(tid)

        self._log_op(user_id, "start_detection", {
            "task_group_id": task_group_id, "task_ids": task_ids,
        })
        self._log_rt("detection_queued", f"任务组 {task_group_id} 已入队, 共 {len(task_ids)} 个子任务")

        return {"success": True, "task_group_id": task_group_id, "task_ids": task_ids}

    async def execute_detection_task(self, task_id: str, task_params: dict) -> dict:
        await self._task_queue.update_task_status(task_id, TaskStatus.RUNNING)
        self._log_rt("task_started", f"子任务 {task_id} 开始执行")

        model_id = task_params["model_id"]
        user_id = str(task_params["user_id"])
        detection_type = task_params.get("detection_type", "static")
        max_iterations = task_params.get("max_iterations", 3)
        raw_ds_id = task_params.get("dataset_id")

        try:
            dataset_ids = [int(raw_ds_id)] if raw_ds_id is not None else None
            if detection_type == "static":
                result = await self._detector.run_static_detection(model_id, user_id, dataset_ids)
            elif detection_type == "dynamic":
                static_result = task_params.get("static_result", {})
                result = await self._detector.run_dynamic_detection(
                    model_id, user_id, static_result, max_iterations
                )
            else:
                static_result = await self._detector.run_static_detection(model_id, user_id, dataset_ids)
                if static_result["status"] != "completed":
                    result = static_result
                else:
                    dynamic_result = await self._detector.run_dynamic_detection(
                        model_id, user_id, static_result, max_iterations
                    )
                    result = {
                        "status": "completed",
                        "static_task_group_id": static_result["task_group_id"],
                        "dynamic_task_group_id": dynamic_result.get("task_group_id"),
                    }
            await self._task_queue.update_task_status(task_id, TaskStatus.COMPLETED)
            self._log_rt("task_completed", f"子任务 {task_id} 执行完成")
            return {"success": True, "task_id": task_id, "result": result}
        except Exception as e:
            await self._task_queue.update_task_status(task_id, TaskStatus.FAILED)
            self._log_err("DetectionError", f"子任务 {task_id} 异常: {e}")
            return {"success": False, "task_id": task_id, "error": str(e)}

    async def execute_concurrent_tasks(self, max_concurrency: int = 3) -> dict:
        batch = await self._task_queue.dequeue_tasks(max_concurrency)
        if not batch:
            self._fsm.detection_done()
            self._notify_state()
            return {"success": True, "tasks": [], "message": "队列为空"}

        async def _run(task) -> dict:
            params = {
                "model_id": task.model_id,
                "user_id": task.user_id,
                "detection_type": task.algorithm_type,
                "dataset_id": task.dataset_id,
                "max_iterations": task.metadata.get("max_iterations", 3),
            }
            return await self.execute_detection_task(task.task_id, params)

        async with asyncio.TaskGroup() as tg:
            futures = [tg.create_task(_run(task)) for task in batch]

        results = [f.result() for f in futures]

        queue_view = await self._task_queue.get_queue_view()
        has_pending = any(t.status == TaskStatus.PENDING for t in queue_view)
        if not has_pending:
            try:
                self._fsm.detection_done()
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
        return {"success": True, "queue": [
            {"task_id": t.task_id, "status": t.status.value, "model_id": t.model_id, "dataset_id": t.dataset_id}
            for t in queue_view
        ]}

    # ── 报告管理调度 (职责 5-8) ──

    async def generate_report(self, task_group_id: str, detection_type: str) -> dict:
        try:
            self._fsm.start_report()
            self._notify_state()
        except Exception:
            return {"success": False, "error": "系统状态不允许生成报告"}

        try:
            if detection_type == "static":
                report = await self._report.generate_static_report(task_group_id)
            else:
                report = await self._report.generate_dynamic_report(task_group_id)
            self._fsm.report_done()
            self._notify_state()
            self._log_rt("report_generated", f"报告已生成: {task_group_id}")
            return {"success": True, "report": report}
        except Exception as e:
            self._handle_error(e, "ReportError")
            return {"success": False, "error": str(e)}

    async def view_report(self, task_group_id: str) -> dict:
        report = await self._report.view_report(task_group_id)
        return {"success": True, "report": report}

    async def list_reports(self, filters: Optional[dict] = None) -> list:
        f = filters or {}
        return await self._report.list_reports(
            user_id=f.get("user_id"), model_id=f.get("model_id"),
        )

    async def delete_report(
        self, target_id: str, caller_user_id: int, granularity: str = "task_group"
    ) -> dict:
        has_access = await self._dac.check_access(int(target_id), caller_user_id)
        if not has_access:
            return {"success": False, "error": "无访问权限"}

        kwargs: dict = {}
        if granularity == "task_group":
            kwargs["task_group_id"] = target_id
        elif granularity == "task":
            kwargs["task_id"] = target_id
        elif granularity == "report":
            kwargs["report_id"] = target_id
        elif granularity == "result_data":
            kwargs["result_data_id"] = target_id

        ok, msg = await self._report.delete_report(**kwargs)
        self._log_op(caller_user_id, "delete_report", {"target_id": target_id, "granularity": granularity})
        return {"success": ok, "message": msg}

    async def export_report(self, task_group_id: str, target_format: str) -> dict:
        content = await self._report.export_report(task_group_id, target_format)
        self._log_rt("report_exported", f"报告 {task_group_id} 已导出为 {target_format}")
        return {"success": True, "content": content}

    async def prepare_visualization_data(self, task_group_id: str) -> dict:
        data = await self._report.prepare_visualization_data(task_group_id)
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

    def get_comm_public_key(self) -> str:
        return self._secure_comm.get_public_key_spki_b64()

    async def query_logs(self, filters: Optional[dict] = None) -> list:
        f = filters or {}
        category = None
        cat_str = f.get("category")
        if cat_str:
            category = LogCategory(cat_str)
        entries = self._logger.query_logs(
            category=category,
            time_start=f.get("time_start"),
            time_end=f.get("time_end"),
            source_module=f.get("source_module"),
            user_id=f.get("user_id"),
        )
        return [
            {
                "log_id": e.log_id,
                "category": e.category.value,
                "level": e.level.value,
                "timestamp": e.timestamp.isoformat(),
                "source_module": e.source_module,
                "user_id": e.user_id,
                "event_type": e.event_type,
                "description": e.description,
                "context": e.context,
            }
            for e in entries
        ]

    def _handle_error(self, exc: Exception, err_type: str) -> None:
        self._log_err(err_type, str(exc))
        self._notify_error(err_type, str(exc))
        try:
            self._fsm.to_error()
            self._notify_state()
        except Exception:
            pass
        try:
            self._fsm.recover()
            self._notify_state()
        except Exception:
            pass

    # ── 用户账号调度 (职责 13-14) ──

    async def schedule_user_auth(
        self, username: str, password: str, action: str, is_encrypted: bool = False
    ) -> dict:
        if is_encrypted:
            pwd = self._secure_comm.decrypt_from_client(base64.b64decode(password))
        else:
            pwd = password

        if action == "register":
            ok, msg = await self._account.register(username, pwd)
            if ok:
                self._log_op(0, "register", {"username": username})
            return {"success": ok, "message": msg}

        if action == "login":
            ok, user_id, error_msg = await self._account.login(username, pwd)
            if ok:
                self._log_op(user_id or 0, "login", {"username": username})
                return {"success": True, "user_id": user_id}
            return {"success": False, "message": error_msg}

        return {"success": False, "error": f"未知操作: {action}"}

    async def schedule_account_operation(self, operation: str, params: dict) -> dict:
        dispatch = {
            "change_password": self._op_change_password,
            "switch_account": self._op_switch_account,
            "logout": self._op_logout,
            "unregister": self._op_unregister,
            "get_profile": self._op_get_profile,
            "update_profile": self._op_update_profile,
            "list_resources": self._op_list_resources,
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
        if p.get("is_encrypted"):
            old_pwd = self._secure_comm.decrypt_from_client(base64.b64decode(old_pwd))
            new_pwd = self._secure_comm.decrypt_from_client(base64.b64decode(new_pwd))
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
        return {"success": True, "resources": resources}

    # ── 权限授权调度 (职责 15-16) ──

    async def schedule_dac_operation(self, operation: str, params: dict) -> dict:
        caller = params["caller_user_id"]

        if operation == "grant":
            ok, msg = await self._dac.grant_access(
                params["resource_id"], params["target_user_id"], caller,
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
                self._fsm.start_configuring()
                self._notify_state()
            except Exception:
                return {"success": False, "error": "系统状态不允许修改配置"}

        try:
            if operation == "create":
                ok, cid = await self._config.create_config(user_id, params["config_content"])
                self._log_op(user_id, "create_config", {"config_id": cid})
                return {"success": ok, "config_id": cid}

            if operation in ("read", "update", "delete", "export"):
                config_id: int = params["config_id"]
                has_access = await self._dac.check_access(config_id, user_id)
                if not has_access:
                    return {"success": False, "error": "无访问权限"}

            if operation == "read":
                data = await self._config.read_config(params["config_id"])
                return {"success": data is not None, "config": data}

            if operation == "update":
                ok, msg = await self._config.update_config(params["config_id"], params["config_content"])
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
                if params.get("is_encrypted"):
                    file_content = self._secure_comm.decrypt_from_client(base64.b64decode(file_content))
                ok, cid = await self._config.import_config(file_content, user_id)
                self._log_op(user_id, "import_config", {"config_id": cid})
                return {"success": ok, "config_id": cid}

            return {"success": False, "error": f"未知配置操作: {operation}"}
        finally:
            if is_write:
                try:
                    self._fsm.configuring_done()
                    self._notify_state()
                except Exception:
                    pass

    async def query_available_datasets(self) -> list:
        datasets = await self._config.query_datasets()
        self._log_rt("query_datasets", "查询可用检测数据集清单")
        return datasets

    async def schedule_private_resource_operation(
        self, operation: str, params: dict
    ) -> dict:
        try:
            self._fsm.start_configuring()
            self._notify_state()
        except Exception:
            return {"success": False, "error": "系统状态不允许修改配置"}

        user_id: int = params.get("user_id", 0)
        try:
            if operation == "upload_adapter":
                adapter_content = params["adapter_content"]
                if params.get("is_encrypted"):
                    adapter_content = self._secure_comm.decrypt_from_client(base64.b64decode(adapter_content))
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
                self._fsm.configuring_done()
                self._notify_state()
            except Exception:
                pass
