"""报告相关 Pydantic 模型"""

from typing import Optional

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    task_group_id: str


class ReportDeleteRequest(BaseModel):
    target_id: str
    granularity: str = "task_group"


class ReportExportRequest(BaseModel):
    task_group_id: str
    target_format: str = "json"
    task_id: str | None = None


class ReportListFilters(BaseModel):
    user_id: Optional[str] = None
    model_id: Optional[str] = None
