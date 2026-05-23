import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

_PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
    "/api/auth/public-key",
    "/docs",
    "/openapi.json",
    "/",
    "/health",
    "/api/status",
}


async def _user_exists_in_db(user_id: int) -> bool:
    """验证 user_id 是否在数据库中真实存在"""
    try:
        from sdpj.ui.webui.backend.dependencies import get_scheduler

        scheduler = get_scheduler()
        result = await scheduler.schedule_account_operation("get_profile", {"user_id": user_id})
        return result.get("success", False) is True
    except Exception:
        # 数据库未就绪或其他异常时降级放行，避免阻断启动阶段
        logger.warning("AuthMiddleware: 用户存在性校验异常，降级放行", exc_info=True)
        return True


class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        if request.url.path in _PUBLIC_PATHS or request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        user_id = request.session.get("user_id")
        if not user_id:
            response = JSONResponse(
                {"success": False, "data": None, "message": "未登录"}, status_code=401
            )
            await response(scope, receive, send)
            return

        # 验证 session 中的 user_id 在数据库中是否仍存在
        # 数据库被删除重建后，旧 session 的 user_id 可能已失效
        if not await _user_exists_in_db(int(user_id)):
            request.session.clear()
            response = JSONResponse(
                {"success": False, "data": None, "message": "用户不存在或已被注销，请重新登录"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})
        scope["state"]["user_id"] = user_id
        await self.app(scope, receive, send)
