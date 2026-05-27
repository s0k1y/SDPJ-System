"""报告相关 Pydantic 模型."""


from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):  # noqa: D101
    task_group_id: str


class ReportDeleteRequest(BaseModel):  # noqa: D101
    target_id: str
    granularity: str = "task_group"


class ReportExportRequest(BaseModel):  # noqa: D101
    task_group_id: str
    target_format: str = "json"
    task_id: str | None = None


class ReportListFilters(BaseModel):  # noqa: D101
    user_id: str | None = None
    model_id: str | None = None
