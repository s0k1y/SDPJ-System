"""报告路由 (职责 4-7)"""
from fastapi import APIRouter, Depends, Request
from typing import Optional

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.schemas.report import (
    ReportGenerateRequest,
    ReportDeleteRequest,
    ReportExportRequest,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
async def generate(
    req: ReportGenerateRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.generate_report(req.task_group_id, req.detection_type)


@router.get("/list")
async def list_reports(
    user_id: Optional[str] = None,
    model_id: Optional[str] = None,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if model_id:
        filters["model_id"] = model_id
    return await scheduler.list_reports(filters or None)


@router.get("/{task_group_id}")
async def view_report(
    task_group_id: str,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.view_report(task_group_id)


@router.delete("/{target_id}")
async def delete_report(
    target_id: str,
    request: Request,
    granularity: str = "task_group",
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    user_id: int = request.state.user_id
    return await scheduler.delete_report(target_id, user_id, granularity)


@router.post("/export")
async def export_report(
    req: ReportExportRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.export_report(req.task_group_id, req.target_format)


@router.get("/{task_group_id}/visualization")
async def visualization(
    task_group_id: str,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.prepare_visualization_data(task_group_id)
