from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_PUBLIC_PATHS = {
    "/api/auth/login", "/api/auth/register", "/api/auth/logout",
    "/api/auth/public-key", "/docs", "/openapi.json", "/", "/health", "/api/status",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in _PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse({"detail": "未登录"}, status_code=401)
        request.state.user_id = user_id
        return await call_next(request)
