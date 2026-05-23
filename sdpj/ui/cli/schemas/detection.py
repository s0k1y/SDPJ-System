"""检测命令输入验证 — 对齐 WebUI schemas/detection.py"""

from typing import Union

from pydantic import BaseModel


class DetectionStartParams(BaseModel):
    model_id: Union[str, int]
    detection_type: str = "static"
    dataset_ids: list[int] = []
    jailbreak_dataset_ids: list[int] = []
    config_id: int | None = None
    max_iterations: int = 3
    force_refresh: bool = False
