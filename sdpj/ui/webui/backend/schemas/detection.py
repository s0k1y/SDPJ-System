"""检测相关 Pydantic 模型."""


from pydantic import BaseModel


class DetectionStartRequest(BaseModel):  # noqa: D101
    model_id: str | int
    detection_type: str = "static"
    dataset_ids: list[int] = []
    jailbreak_dataset_ids: list[int] = []
    config_id: int | None = None
    max_iterations: int = 3
    force_refresh: bool = False
    encoding_types: list[str] | None = None
    modalities: list[str] | None = None
    has_direct: bool = True


class ConcurrentRunRequest(BaseModel):  # noqa: D101
    max_concurrency: int = 3


class ConfigOperationRequest(BaseModel):  # noqa: D101
    operation: str
    params: dict = {}


class CancelTaskRequest(BaseModel):  # noqa: D101
    task_id: str | None = None
    task_group_id: str | None = None


class PrivateResourceRequest(BaseModel):  # noqa: D101
    operation: str
    params: dict = {}
