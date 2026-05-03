"""检测相关 Pydantic 模型"""
from pydantic import BaseModel
from typing import Optional


class DetectionStartRequest(BaseModel):
    model_id: str
    detection_type: str = "static"
    dataset_ids: list[int] = []
    config_id: Optional[int] = None
    max_iterations: int = 3


class ConcurrentRunRequest(BaseModel):
    max_concurrency: int = 3


class ConfigOperationRequest(BaseModel):
    operation: str
    params: dict = {}


class PrivateResourceRequest(BaseModel):
    operation: str
    params: dict = {}
