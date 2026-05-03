"""ResultDB 模块

检测结果数据库模块，提供检测任务、报告和结果数据的持久化能力。
"""

from .interface import ResultDBInterface
from .result_db import ResultDB
from .session import SessionManager
from .models import (
    Base,
    TaskGroup,
    DetectionTask,
    DetectionReport,
    ResultData,
)

__all__ = [
    "ResultDBInterface",
    "ResultDB",
    "SessionManager",
    "Base",
    "TaskGroup",
    "DetectionTask",
    "DetectionReport",
    "ResultData",
]
