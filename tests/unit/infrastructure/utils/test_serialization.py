from sdpj.infrastructure.utils.serialization import (
    serialize_json, deserialize_json,
    serialize_yaml, deserialize_yaml,
)


def test_json_roundtrip():
    obj = {"key": "value", "num": 42}
    assert deserialize_json(serialize_json(obj)) == obj


def test_json_unicode():
    obj = {"msg": "你好"}
    assert "你好" in serialize_json(obj)


def test_yaml_roundtrip():
    obj = {"key": "value", "list": [1, 2, 3]}
    assert deserialize_yaml(serialize_yaml(obj)) == obj
