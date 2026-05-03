"""WebSocket 路由 — 实时状态与异常推送 (职责 8, 10)"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/status")
async def status_ws(
    websocket: WebSocket,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def on_state(state: str) -> None:
        queue.put_nowait({"type": "state", "data": state})

    def on_error(err_type: str, desc: str) -> None:
        queue.put_nowait({"type": "error", "err_type": err_type, "data": desc})

    scheduler.subscribe_state_changes(on_state)
    scheduler.subscribe_errors(on_error)
    queue.put_nowait({"type": "state", "data": scheduler.get_system_state()})
    try:
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=30)
            await websocket.send_json(msg)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        scheduler.unsubscribe_state_changes(on_state)
        scheduler.unsubscribe_errors(on_error)


@router.websocket("/ws/task/{task_id}")
async def task_progress_ws(
    task_id: str,
    websocket: WebSocket,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
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
                await websocket.send_json({"type": "progress", "task_id": task_id, "status": status})
            if status in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

