"""报告命令输入验证 — 对齐 WebUI schemas/report.py"""

from pydantic import BaseModel


class ReportGenerateParams(BaseModel):
    task_group_id: str
    detection_type: str = "static"


class ReportExportParams(BaseModel):
    task_group_id: str
    target_format: str = "json"
    task_id: str | None = None
