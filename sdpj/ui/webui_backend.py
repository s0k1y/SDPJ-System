"""WebUI Backend API"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sdpj.control.state_scheduler import StateScheduler

scheduler = StateScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await scheduler.init()
    yield
    # 关闭时清理（如需要）


app = FastAPI(title="SDPJ-System API", lifespan=lifespan)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class DetectionRequest(BaseModel):
    model_id: str
    dataset_id: int
    algorithm_type: str = "static"


@app.get("/")
async def root():
    """根路径"""
    return {"message": "SDPJ-System API", "version": "1.0.0"}


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    state = scheduler.get_system_state()
    return {"status": state}


@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """用户注册"""
    result = await scheduler.register_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """用户登录"""
    result = await scheduler.login_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail="登录失败")
    return result


@app.post("/api/detection/start")
async def start_detection(req: DetectionRequest):
    """启动检测任务"""
    config_data = {
        "model_id": req.model_id,
        "dataset_id": req.dataset_id,
        "algorithm_type": req.algorithm_type
    }
    result = await scheduler.start_detection(user_id=1, config_data=config_data)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/api/detection/progress/{task_id}")
async def get_progress(task_id: str):
    """查询检测进度"""
    result = await scheduler.query_detection_progress(task_id)
    return result


@app.get("/api/report/{task_group_id}")
async def get_report(task_group_id: int):
    """获取检测报告"""
    result = await scheduler.generate_report(task_group_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
