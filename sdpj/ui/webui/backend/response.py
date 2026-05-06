"""统一 API 响应格式"""
from typing import Any, Optional

from sdpj.infrastructure.utils.serialization import ensure_utc_datetimes


def success_response(data: Any = None, message: str = "") -> dict:
    return {"success": True, "data": ensure_utc_datetimes(data), "message": message}


def error_response(message: str = "操作失败", data: Any = None) -> dict:
    return {"success": False, "data": ensure_utc_datetimes(data), "message": message}


def wrap_scheduler_result(result: Any) -> dict:
    if isinstance(result, dict):
        if result.get("success") is False:
            msg = result.get("error") or result.get("message") or "操作失败"
            data = {k: v for k, v in result.items() if k not in ("success", "error", "message")}
            return error_response(message=msg, data=data if data else None)
        data = {k: v for k, v in result.items() if k not in ("success", "error", "message")}
        msg = result.get("message", "")
        return success_response(data=data, message=msg)
    return success_response(data=result)
