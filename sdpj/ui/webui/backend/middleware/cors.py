"""CORS 中间件配置"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    配置 CORS 中间件

    注意：allow_credentials=True 时不能使用 allow_origins=["*"]
    全链路 HTTPS 后仅允许 https 源，开发环境保留 http 回退
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://localhost:5173",   # Vite 开发服务器 (HTTPS)
            "https://localhost:3000",   # 备用端口 (HTTPS)
            "https://127.0.0.1:5173",
            "https://127.0.0.1:3000",
            "http://localhost:5173",    # 回退（证书未就绪时）
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
