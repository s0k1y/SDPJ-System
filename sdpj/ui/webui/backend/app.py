"""FastAPI 应用组装"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from starlette.middleware.sessions import SessionMiddleware

from sdpj.ui.webui.backend.middleware.cors import setup_cors
from sdpj.ui.webui.backend.middleware.auth import AuthMiddleware
from sdpj.ui.webui.backend.routers import auth, detection, reports, users, websocket


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
    app.add_middleware(AuthMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=get_settings().resolve_secret_key())

    app.include_router(auth.router)
    app.include_router(detection.router)
    app.include_router(reports.router)
    app.include_router(users.router)
    app.include_router(websocket.router)

    @app.get("/")
    async def root():
        return {"message": "SDPJ-System API", "version": "1.0.0"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/status")
    async def status():
        from sdpj.ui.webui.backend.dependencies import get_scheduler
        return {"status": get_scheduler().get_system_state()}

    @app.get("/api/logs")
    async def logs(category: str = None, source_module: str = None, user_id: str = None):
        from sdpj.ui.webui.backend.dependencies import get_scheduler
        filters = {}
        if category:
            filters["category"] = category
        if source_module:
            filters["source_module"] = source_module
        if user_id:
            filters["user_id"] = user_id
        return await get_scheduler().query_logs(filters or None)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sdpj.ui.webui.backend.app:app", host="0.0.0.0", port=8000, reload=True)
