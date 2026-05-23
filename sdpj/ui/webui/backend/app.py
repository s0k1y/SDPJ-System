"""FastAPI 应用组装"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from sdpj.core.secure_comm_manager import SecureCommManager
from sdpj.ui.webui.backend.middleware.auth import AuthMiddleware
from sdpj.ui.webui.backend.middleware.cors import setup_cors
from sdpj.ui.webui.backend.response import success_response
from sdpj.ui.webui.backend.routers import auth, detection, reports, users, websocket

SYSTEM_USERNAME = "SDPJ-System"
SYSTEM_USER_IDS = (None, "0", "system")

# 安全通信管理器（单例）
_secure_comm = SecureCommManager()


class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件，由 SecureCommManager 提供头部配置"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header_name, header_value in _secure_comm.get_security_headers().items():
            response.headers[header_name] = header_value
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from sdpj.ui.webui.backend.dependencies import get_scheduler

    scheduler = get_scheduler()
    await scheduler.startup()
    yield
    await scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="SDPJ-System API", version="1.0.0", lifespan=lifespan)

    from sdpj.infrastructure.config.settings import get_settings

    setup_cors(app)
    app.add_middleware(_SecurityHeadersMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=get_settings().resolve_secret_key(),
        same_site="lax",
        https_only=True,
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "message": exc.detail},
        )

    app.include_router(auth.router)
    app.include_router(detection.router)
    app.include_router(reports.router)
    app.include_router(users.router)
    app.include_router(websocket.router)

    @app.get("/")
    async def root():
        return success_response(data={"name": "SDPJ-System API", "version": "1.0.0"})

    @app.get("/health")
    async def health():
        return success_response(data={"status": "ok"})

    @app.get("/api/status")
    async def status():
        from sdpj.ui.webui.backend.dependencies import get_scheduler

        return success_response(data={"status": get_scheduler().get_system_state()})

    @app.get("/api/logs")
    async def logs(
        request: Request,
        level: str = None,
        source_module: str = None,
        user_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ):
        from sdpj.ui.webui.backend.dependencies import get_scheduler

        scheduler = get_scheduler()

        filters = {}
        if level:
            filters["level"] = level
        if source_module:
            filters["source_module"] = source_module

        if user_id == SYSTEM_USERNAME:
            filters["user_ids"] = list(SYSTEM_USER_IDS)
        elif user_id:
            filters["user_id"] = user_id

        filters["page"] = page
        filters["page_size"] = page_size

        result = await scheduler.query_logs(filters or None)
        logs_data = result.get("logs", [])
        total = result.get("total", 0)

        all_users = await scheduler.list_all_users()
        user_map = {str(u["user_id"]): u["username"] for u in all_users}

        for log in logs_data:
            uid = log.get("user_id")
            if uid and uid not in SYSTEM_USER_IDS:
                log["username"] = user_map.get(str(uid), f"User#{uid}")
            else:
                log["username"] = SYSTEM_USERNAME

        return success_response(data={"logs": logs_data, "total": total})

    @app.get("/api/logs/users")
    async def logs_users(request: Request):
        from sdpj.ui.webui.backend.dependencies import get_scheduler

        result = await get_scheduler().query_logs({"category": "operation"})
        all_logs = result.get("logs", [])
        unique_user_ids = set()
        for log in all_logs:
            if log.get("user_id") and log["user_id"] not in SYSTEM_USER_IDS:
                unique_user_ids.add(str(log["user_id"]))

        all_users = await get_scheduler().list_all_users()
        user_map = {str(u["user_id"]): u["username"] for u in all_users}

        usernames = [user_map.get(uid, f"User#{uid}") for uid in unique_user_ids if uid in user_map]
        return success_response(data={"users": sorted(usernames)})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    from sdpj.infrastructure.config.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "sdpj.ui.webui.backend.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        **_secure_comm.get_ssl_kwargs(),
    )
