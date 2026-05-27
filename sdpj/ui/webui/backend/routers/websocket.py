"""WebSocket 路由 — 实时状态,异常与日志推送 (职责 8, 10)."""

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/status")
async def status_ws(  # noqa: D103
    websocket: WebSocket,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),  # noqa: B008
) -> None:
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def on_state(state: str) -> None:
        queue.put_nowait({"type": "state", "data": state})

    def on_error(err_type: str, desc: str) -> None:
        queue.put_nowait({"type": "error", "err_type": err_type, "data": desc})

    scheduler.subscribe_state_changes(on_state)
    scheduler.subscribe_errors(on_error)
    queue.put_nowait({"type": "state", "data": scheduler.get_system_state()})

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(25)
            queue.put_nowait({"__hb__": True})

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=30)
            if msg.get("__hb__"):
                await websocket.send_json({"type": "heartbeat"})
                continue
            await websocket.send_json(msg)
    except (TimeoutError, WebSocketDisconnect):
        pass
    finally:
        hb_task.cancel()
        scheduler.unsubscribe_state_changes(on_state)
        scheduler.unsubscribe_errors(on_error)


@router.websocket("/ws/logs")
async def logs_ws(  # noqa: D103
    websocket: WebSocket,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),  # noqa: B008
) -> None:
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def on_new_log(log_data: dict) -> None:
        queue.put_nowait(log_data)

    scheduler.subscribe_logs(on_new_log)

    all_users = await scheduler.list_all_users()
    user_map = {str(u["user_id"]): u["username"] for u in all_users}

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(25)
            queue.put_nowait({"__hb__": True})

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=30)
            if msg.get("__hb__"):
                await websocket.send_json({"type": "heartbeat"})
                continue
            uid = msg.get("user_id")
            if uid and uid not in (None, "0", "system"):
                msg["username"] = user_map.get(str(uid), f"User#{uid}")
            else:
                msg["username"] = "SDPJ-System"
            await websocket.send_json({"type": "log", "data": msg})
    except (TimeoutError, WebSocketDisconnect):
        pass
    finally:
        hb_task.cancel()
        scheduler.unsubscribe_logs(on_new_log)


@router.websocket("/ws/task/{task_id}")
async def task_progress_ws(  # noqa: D103
    task_id: str,
    websocket: WebSocket,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),  # noqa: B008
) -> None:
    await websocket.accept()
    last_status = None
    try:
        while True:
            result = await scheduler.query_detection_progress(task_id)
            if not result.get("success"):
                await websocket.send_json({"type": "error", "data": result.get("error")})
                break
            status = result["status"]
            if status != last_status:
                last_status = status
                await websocket.send_json(
                    {"type": "progress", "task_id": task_id, "status": status},
                )
            if status in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
