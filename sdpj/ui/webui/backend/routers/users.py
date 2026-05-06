"""用户管理与权限路由 (职责 12-14)"""
from fastapi import APIRouter, Depends, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.response import success_response, wrap_scheduler_result
from sdpj.ui.webui.backend.schemas.user import AccountOperationRequest, DACOperationRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/account")
async def account_operation(
    req: AccountOperationRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "user_id": request.state.user_id}
    return wrap_scheduler_result(await scheduler.schedule_account_operation(req.operation, params))


@router.get("/profile")
async def profile(
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.schedule_account_operation("get_profile", {"user_id": request.state.user_id}))


@router.get("/resources")
async def resources(
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    return wrap_scheduler_result(await scheduler.schedule_account_operation("list_resources", {"user_id": request.state.user_id}))


@router.post("/dac")
async def dac_operation(
    req: DACOperationRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    params = {**req.params, "caller_user_id": request.state.user_id}
    return wrap_scheduler_result(await scheduler.schedule_dac_operation(req.operation, params))


@router.get("/dac/check")
async def check_access(
    resource_id: int,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    has_access = await scheduler.check_resource_access(resource_id, request.state.user_id)
    return success_response(data={"has_access": has_access})
