"""检测路由 (职责 1-3)"""
from fastapi import APIRouter, Depends, Request, UploadFile, File

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.response import success_response, error_response, wrap_scheduler_result
from sdpj.ui.webui.backend.schemas.detection import (
    DetectionStartRequest,
    ConcurrentRunRequest,
    CancelTaskRequest,
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
    return wrap_scheduler_result(await scheduler.start_detection(user_id, config_data))


@router.post("/run")
async def run_concurrent(
    req: ConcurrentRunRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.execute_concurrent_tasks(req.max_concurrency))


@router.get("/progress")
async def progress_all(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.query_detection_progress())


@router.get("/progress/{task_id}")
async def progress_single(
    task_id: str,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.query_detection_progress(task_id))


@router.post("/cancel")
async def cancel_task(
    req: CancelTaskRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    if req.task_group_id:
        return wrap_scheduler_result(await scheduler.cancel_task_group(req.task_group_id))
    if req.task_id:
        return wrap_scheduler_result(await scheduler.cancel_task(req.task_id))
    return error_response(message="必须提供 task_id 或 task_group_id")


@router.get("/datasets")
async def datasets(
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id = request.state.user_id
    result = await scheduler.query_available_datasets(user_id)
    return success_response(data=result)


@router.get("/datasets/{dataset_id}")
async def dataset_detail(
    dataset_id: int,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id = request.state.user_id
    dataset = await scheduler.query_dataset_detail(dataset_id, user_id)
    if dataset:
        return success_response(data={"dataset": dataset})
    return error_response(message="数据集不存在")


@router.get("/datasets/{dataset_id}/export")
async def export_dataset(
    dataset_id: int,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    from fastapi.responses import Response

    try:
        user_id = request.state.user_id
        dataset_file = await scheduler.export_dataset_file(dataset_id, user_id)
        if not dataset_file:
            return error_response(message="数据集不存在")

        if "error" in dataset_file and "content" not in dataset_file:
            return error_response(message=dataset_file["error"])

        content = dataset_file['content']
        if isinstance(content, str):
            content = content.encode('utf-8')

        return Response(
            content=content,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{dataset_file["filename"]}"'
            }
        )
    except Exception as e:
        import traceback
        print(f"导出数据集错误: {e}")
        print(traceback.format_exc())
        return error_response(message=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id = request.state.user_id
    result = await scheduler.delete_user_dataset(dataset_id, user_id)
    if result.get("success"):
        return success_response(message="删除成功")
    return error_response(message=result.get("error", "删除失败"))


@router.post("/datasets/import")
async def import_dataset(
    request: Request,
    file: UploadFile = File(...),
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id = request.state.user_id

    try:
        content = await file.read()

        result = await scheduler.import_dataset_file(
            user_id=user_id,
            filename=file.filename,
            content=content
        )

        if result.get("success"):
            return success_response(data={"dataset_id": result.get("dataset_id")}, message="导入成功")
        else:
            return error_response(message=result.get("error", "导入失败"))
    except Exception as e:
        import traceback
        print(f"导入数据集错误: {e}")
        print(traceback.format_exc())
        return error_response(message=str(e))


@router.post("/config")
async def config_operation(
    req: ConfigOperationRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "user_id": request.state.user_id}
    return wrap_scheduler_result(await scheduler.schedule_config_operation(req.operation, params))


@router.post("/resource")
async def resource_operation(
    req: PrivateResourceRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "user_id": request.state.user_id}
    return wrap_scheduler_result(await scheduler.schedule_private_resource_operation(req.operation, params))
