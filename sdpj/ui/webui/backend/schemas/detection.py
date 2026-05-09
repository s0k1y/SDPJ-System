"""检测相关 Pydantic 模型"""

from typing import Optional, Union

from pydantic import BaseModel


class DetectionStartRequest(BaseModel):
    model_id: Union[str, int]
    detection_type: str = "static"
    dataset_ids: list[int] = []
    jailbreak_dataset_ids: list[int] = []
    config_id: Optional[int] = None
    max_iterations: int = 3
    force_refresh: bool = False


class ConcurrentRunRequest(BaseModel):
    max_concurrency: int = 3


class ConfigOperationRequest(BaseModel):
    operation: str
    params: dict = {}


class CancelTaskRequest(BaseModel):
    task_id: str | None = None
    task_group_id: str | None = None


class PrivateResourceRequest(BaseModel):
    operation: str
    params: dict = {}
