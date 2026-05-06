"""UtilsLib 序列化工具"""
import json
import yaml
from datetime import datetime, timezone
from typing import Any


def serialize_json(obj: dict) -> str:
    """JSON 序列化"""
    return json.dumps(obj, ensure_ascii=False, indent=2)


def deserialize_json(text: str) -> dict:
    """JSON 反序列化"""
    return json.loads(text)


def serialize_yaml(obj: dict) -> str:
    """YAML 序列化"""
    return yaml.dump(obj, allow_unicode=True)


def deserialize_yaml(text: str) -> dict:
    """YAML 反序列化"""
    return yaml.safe_load(text)


def to_utc_iso(dt: datetime | None) -> str | None:
    """将 datetime 转换为 ISO 8601 带时区字符串

    naive datetime 视为 UTC，aware datetime 保持原时区。
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def ensure_utc_datetimes(data: Any) -> Any:
    """递归处理数据中的 naive datetime 对象，为其添加 UTC 时区信息

    原地修改 dict/list，确保 FastAPI 序列化时输出带时区的 ISO 8601 字符串。
    """
    if isinstance(data, datetime):
        if data.tzinfo is None:
            return data.replace(tzinfo=timezone.utc)
        return data
    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = ensure_utc_datetimes(v)
        return data
    if isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = ensure_utc_datetimes(item)
        return data
    return data
