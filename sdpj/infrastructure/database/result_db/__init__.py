"""ResultDB 模块.

检测结果数据库模块,提供检测任务,报告和结果数据的持久化能力.
"""

from .interface import ResultDBInterface
from .models import (
    Base,
    DetectionReport,
    DetectionTask,
    ResultData,
    SystemLog,
    TaskGroup,
)
from .result_db import ResultDB
from .session import SessionManager

__all__ = [
    "Base",
    "DetectionReport",
    "DetectionTask",
    "ResultDB",
    "ResultDBInterface",
    "ResultData",
    "SessionManager",
    "SystemLog",
    "TaskGroup",
]
