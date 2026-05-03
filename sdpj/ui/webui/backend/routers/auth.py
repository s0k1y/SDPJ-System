"""认证路由 (职责 11)"""
from fastapi import APIRouter, Depends, HTTPException, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.schemas.user import AuthRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/public-key")
def get_public_key(scheduler: StateSchedulerInterface = Depends(get_scheduler)):
    return {"public_key": scheduler.get_comm_public_key()}


@router.post("/register")
async def register(
    req: AuthRequest,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    result = await scheduler.schedule_user_auth(
        req.username, req.password, "register", is_encrypted=req.is_encrypted,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message", "注册失败"))
    return result


@router.post("/login")
async def login(
    req: AuthRequest,
    request: Request,
    scheduler: StateSchedulerInterface = Depends(get_scheduler),
):
    result = await scheduler.schedule_user_auth(
        req.username, req.password, "login", is_encrypted=req.is_encrypted,
    )
    if not result["success"]:
        raise HTTPException(status_code=401, detail="登录失败")
    request.session["user_id"] = result.get("user_id", 0)
    return {"success": True, "user_id": result.get("user_id")}


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True}
