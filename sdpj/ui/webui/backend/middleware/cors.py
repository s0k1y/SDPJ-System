"""CORS 中间件配置"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    配置 CORS 中间件

    注意：allow_credentials=True 时不能使用 allow_origins=["*"]
    开发环境允许 localhost，生产环境应配置具体的前端域名
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite 开发服务器
            "http://localhost:3000",  # 备用端口
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
