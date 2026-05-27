"""CLI 输入验证 Schemas — 对齐 WebUI Pydantic 模型."""

from sdpj.ui.cli.schemas.detection import DetectionStartParams
from sdpj.ui.cli.schemas.report import ReportExportParams, ReportGenerateParams
from sdpj.ui.cli.schemas.user import AccountOpParams, AuthParams, DACOpParams

__all__ = [
    "AccountOpParams",
    "AuthParams",
    "DACOpParams",
    "DetectionStartParams",
    "ReportExportParams",
    "ReportGenerateParams",
]
