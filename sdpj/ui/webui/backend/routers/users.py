"""用户管理与权限路由 (职责 12-14)"""
from fastapi import APIRouter, Depends, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.schemas.user import AccountOperationRequest, DACOperationRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/account")
async def account_operation(
    req: AccountOperationRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.schedule_account_operation(req.operation, req.params)


@router.get("/profile")
async def profile(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.schedule_account_operation("get_profile", {})


@router.get("/resources")
async def resources(
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return await scheduler.schedule_account_operation("list_resources", {})


@router.post("/dac")
async def dac_operation(
    req: DACOperationRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "caller_user_id": request.state.user_id}
    return await scheduler.schedule_dac_operation(req.operation, params)


@router.get("/dac/check")
async def check_access(
    resource_id: int,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    has_access = await scheduler.check_resource_access(resource_id, request.state.user_id)
    return {"has_access": has_access}
