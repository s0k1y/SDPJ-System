"""报告相关 Pydantic 模型"""
from pydantic import BaseModel
from typing import Optional


class ReportGenerateRequest(BaseModel):
    task_group_id: str
    detection_type: str = "static"


class ReportDeleteRequest(BaseModel):
    target_id: str
    granularity: str = "task_group"


class ReportExportRequest(BaseModel):
    task_group_id: str
    target_format: str = "json"


class ReportListFilters(BaseModel):
    user_id: Optional[str] = None
    model_id: Optional[str] = None
