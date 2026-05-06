from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_PUBLIC_PATHS = {
    "/api/auth/login", "/api/auth/register", "/api/auth/logout",
    "/api/auth/public-key", "/docs", "/openapi.json", "/", "/health", "/api/status",
}
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
            response = JSONResponse({"success": False, "data": None, "message": "未登录"}, status_code=401)
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})
        scope["state"]["user_id"] = user_id
        await self.app(scope, receive, send)
