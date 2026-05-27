"""认证路由 (职责 11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from sdpj.control.state_scheduler_interface import StateSchedulerInterface
from sdpj.ui.webui.backend.dependencies import get_scheduler
from sdpj.ui.webui.backend.response import success_response
from sdpj.ui.webui.backend.schemas.user import AuthRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])

_rsa_private_key = None
_rsa_public_key = None


def _get_or_create_rsa_keys():  # noqa: ANN202
    global _rsa_private_key, _rsa_public_key  # noqa: PLW0603
    if _rsa_public_key is None:
        from cryptography.hazmat.backends import default_backend  # noqa: PLC0415
        from cryptography.hazmat.primitives import serialization  # noqa: PLC0415
        from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: PLC0415

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        _rsa_private_key = key
        _rsa_public_key = (
            key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )
    return _rsa_public_key


@router.get("/public-key")
async def public_key():  # noqa: ANN201, D103
    return success_response(data={"public_key": _get_or_create_rsa_keys()})


@router.post("/register")
async def register(  # noqa: ANN201, D103
    req: AuthRequest,
    scheduler: Annotated[StateSchedulerInterface, Depends(get_scheduler)],
):
    result = await scheduler.schedule_user_auth(req.username, req.password, "register")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message", "注册失败"))
    return success_response(
        data={"user_id": result.get("user_id")}, message=result.get("message", ""),
    )


@router.post("/login")
async def login(  # noqa: ANN201, D103
    req: AuthRequest,
    request: Request,
    scheduler: Annotated[StateSchedulerInterface, Depends(get_scheduler)],
):
    result = await scheduler.schedule_user_auth(req.username, req.password, "login")
    if not result["success"]:
        error_msg = result.get("message", "登录失败")
        raise HTTPException(status_code=401, detail=error_msg)
    request.session["user_id"] = result.get("user_id", 0)
    return success_response(data={"user_id": result.get("user_id")})


@router.get("/me")
async def me(  # noqa: ANN201
    request: Request,
    scheduler: Annotated[StateSchedulerInterface, Depends(get_scheduler)],
):
    """返回当前会话用户信息,供前端校验会话有效性."""
    user_id = request.state.user_id
    result = await scheduler.schedule_account_operation("get_profile", {"user_id": user_id})
    profile = result.get("profile")
    if profile is None:
        raise HTTPException(status_code=401, detail="用户不存在或已被注销")
    return success_response(data={"user_id": profile["user_id"], "username": profile["username"]})


@router.post("/logout")
async def logout(request: Request):  # noqa: ANN201, D103
    request.session.clear()
    return success_response()
