"""UtilsLib 序列化工具"""
import json
import yaml


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
