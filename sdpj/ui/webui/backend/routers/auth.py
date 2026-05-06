"""认证路由 (职责 11)"""
from fastapi import APIRouter, Depends, HTTPException, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.response import success_response
from sdpj.ui.webui.backend.schemas.user import AuthRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(
    req: AuthRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    result = await scheduler.schedule_user_auth(req.username, req.password, "register")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message", "注册失败"))
    return success_response(data={"user_id": result.get("user_id")}, message=result.get("message", ""))


@router.post("/login")
async def login(
    req: AuthRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    result = await scheduler.schedule_user_auth(req.username, req.password, "login")
    if not result["success"]:
        error_msg = result.get("message", "登录失败")
        raise HTTPException(status_code=401, detail=error_msg)
    request.session["user_id"] = result.get("user_id", 0)
    return success_response(data={"user_id": result.get("user_id")})


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return success_response()
