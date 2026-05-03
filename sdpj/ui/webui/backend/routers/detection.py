"""检测路由 (职责 1-3)"""
from fastapi import APIRouter, Depends, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.schemas.detection import (
    DetectionStartRequest,
    ConcurrentRunRequest,
    ConfigOperationRequest,
    PrivateResourceRequest,
)

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/start")
async def start_detection(
    req: DetectionStartRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    config_data = req.model_dump()
    return await scheduler.start_detection(user_id, config_data)


@router.post("/run")
async def run_concurrent(
    req: ConcurrentRunRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.execute_concurrent_tasks(req.max_concurrency)


@router.get("/progress")
async def progress_all(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.query_detection_progress()


@router.get("/progress/{task_id}")
async def progress_single(
    task_id: str,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.query_detection_progress(task_id)


@router.get("/datasets")
async def datasets(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.query_available_datasets()


@router.post("/config")
async def config_operation(
    req: ConfigOperationRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "user_id": request.state.user_id}
    return await scheduler.schedule_config_operation(req.operation, params)


@router.post("/resource")
async def resource_operation(
    req: PrivateResourceRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "user_id": request.state.user_id}
    return await scheduler.schedule_private_resource_operation(req.operation, params)
