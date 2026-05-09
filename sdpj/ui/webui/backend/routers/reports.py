"""报告路由 (职责 4-7)"""

from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.response import success_response, wrap_scheduler_result
from sdpj.ui.webui.backend.schemas.report import (
    ReportExportRequest,
    ReportGenerateRequest,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/statistics")
async def compliance_statistics(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.query_compliance_statistics())


@router.post("/generate")
async def generate(
    req: ReportGenerateRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return wrap_scheduler_result(
        await scheduler.generate_report(req.task_group_id, req.detection_type, user_id=user_id)
    )


@router.get("/list")
async def list_reports(
    request: Request,
    model_id: Optional[str] = None,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    filters = {"user_id": user_id}
    if model_id:
        filters["model_id"] = model_id
    result = await scheduler.list_reports(filters)
    return success_response(data=result)


@router.get("/{task_group_id}")
async def view_report(
    task_group_id: str,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return wrap_scheduler_result(await scheduler.view_report(task_group_id, user_id=user_id))


@router.delete("/{target_id}")
async def delete_report(
    target_id: str,
    request: Request,
    granularity: str = "task_group",
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return wrap_scheduler_result(await scheduler.delete_report(target_id, user_id, granularity))


@router.post("/export")
async def export_report(
    req: ReportExportRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    result = await scheduler.export_report(req.task_group_id, req.target_format, user_id=user_id, task_id=req.task_id)
    if not result.get("success"):
        return wrap_scheduler_result(result)
    filename = result.get("filename", f"report.{req.target_format}")
    content = result.get("content", "")
    content_type_map = {
        "json": "application/json",
        "yaml": "application/x-yaml",
        "jsonl": "application/x-ndjson",
    }
    media_type = content_type_map.get(req.target_format, "application/octet-stream")
    return StreamingResponse(
        BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/task/{task_id}/visualization")
async def task_visualization(
    task_id: str,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return wrap_scheduler_result(await scheduler.prepare_task_visualization_data(task_id, user_id=user_id))


@router.get("/{task_group_id}/visualization")
async def visualization(
    task_group_id: str,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return wrap_scheduler_result(await scheduler.prepare_visualization_data(task_group_id, user_id=user_id))
