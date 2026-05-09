"""UtilsLib 数据校验工具"""

from typing import Any


def validate_data(data: Any, schema: dict) -> tuple[bool, str]:
    """根据 schema 校验数据结构

    schema 支持的字段:
        type: "dict" | "list" | "str" | "int" | "float" | "bool"
        required_keys: list[str]  (type=dict 时)
        optional_keys: list[str]  (type=dict 时，允许但不强制)
        allowed_keys: list[str]   (type=dict 时，限制只能出现这些 key)
        min_length / max_length: int  (type=list|str 时)
        min_value / max_value: number (type=int|float 时)
        values_schema: dict       (type=list 时，对每个元素递归校验)
        fields: dict[str, dict]   (type=dict 时，对指定字段递归校验)
    """
    expected_type = schema.get("type")

    if expected_type == "dict":
        if not isinstance(data, dict):
            return False, f"期望 dict，实际为 {type(data).__name__}"
        required = schema.get("required_keys", [])
        missing = [k for k in required if k not in data]
        if missing:
            return False, f"缺少必填字段: {', '.join(missing)}"
        allowed = schema.get("allowed_keys")
        if allowed is not None:
            extra = [k for k in data if k not in allowed]
            if extra:
                return False, f"不允许的字段: {', '.join(extra)}"
        fields = schema.get("fields", {})
        for field_name, field_schema in fields.items():
            if field_name in data:
                ok, msg = validate_data(data[field_name], field_schema)
                if not ok:
                    return False, f"字段 '{field_name}': {msg}"

    elif expected_type == "list":
        if not isinstance(data, list):
            return False, f"期望 list，实际为 {type(data).__name__}"
        min_len = schema.get("min_length", 0)
        max_len = schema.get("max_length")
        if len(data) < min_len:
            return False, f"列表长度 {len(data)} 小于最小要求 {min_len}"
        if max_len is not None and len(data) > max_len:
            return False, f"列表长度 {len(data)} 超过最大限制 {max_len}"
        values_schema = schema.get("values_schema")
        if values_schema:
            for i, item in enumerate(data):
                ok, msg = validate_data(item, values_schema)
                if not ok:
                    return False, f"列表第 {i} 项: {msg}"

    elif expected_type == "str":
        if not isinstance(data, str):
            return False, f"期望 str，实际为 {type(data).__name__}"
        min_len = schema.get("min_length", 0)
        max_len = schema.get("max_length")
        if len(data) < min_len:
            return False, f"字符串长度 {len(data)} 小于最小要求 {min_len}"
        if max_len is not None and len(data) > max_len:
            return False, f"字符串长度 {len(data)} 超过最大限制 {max_len}"

    elif expected_type in ("int", "float"):
        if not isinstance(data, (int, float)):
            return False, f"期望 {expected_type}，实际为 {type(data).__name__}"
        if expected_type == "int" and not isinstance(data, int):
            return False, "期望 int，实际为 float"
        min_val = schema.get("min_value")
        max_val = schema.get("max_value")
        if min_val is not None and data < min_val:
            return False, f"值 {data} 小于最小值 {min_val}"
        if max_val is not None and data > max_val:
            return False, f"值 {data} 超过最大值 {max_val}"

    elif expected_type == "bool":
        if not isinstance(data, bool):
            return False, f"期望 bool，实际为 {type(data).__name__}"

    elif expected_type is not None:
        return False, f"未知的 schema type: {expected_type}"

    return True, ""
