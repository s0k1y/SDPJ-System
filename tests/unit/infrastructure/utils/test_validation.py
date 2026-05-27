"""test_validation 模块单元测试."""

from sdpj.infrastructure.utils.validation import validate_data
from typing import Any


def test_dict_required_keys_pass() -> None:
    """测试 test dict required keys pass."""
    ok, _ = validate_data({"a": 1, "b": 2}, {"type": "dict", "required_keys": ["a", "b"]})
    assert ok


def test_dict_missing_required_key() -> None:
    """测试 test dict missing required key."""
    ok, msg = validate_data({"a": 1}, {"type": "dict", "required_keys": ["a", "b"]})
    assert not ok and "b" in msg


def test_dict_disallowed_key() -> None:
    """测试 test dict disallowed key."""
    ok, msg = validate_data({"a": 1, "x": 2}, {"type": "dict", "allowed_keys": ["a"]})
    assert not ok and "x" in msg


def test_list_min_length() -> None:
    """测试 test list min length."""
    ok, msg = validate_data([], {"type": "list", "min_length": 1})
    assert not ok


def test_list_values_schema() -> None:
    """测试 test list values schema."""
    ok, _ = validate_data([1, 2], {"type": "list", "values_schema": {"type": "int"}})
    assert ok
    ok2, _ = validate_data([1, "x"], {"type": "list", "values_schema": {"type": "int"}})
    assert not ok2


def test_str_length() -> None:
    """测试 test str length."""
    ok, _ = validate_data("hi", {"type": "str", "min_length": 2, "max_length": 5})
    assert ok
    ok2, _ = validate_data("h", {"type": "str", "min_length": 2})
    assert not ok2


def test_int_range() -> None:
    """测试 test int range."""
    ok, _ = validate_data(5, {"type": "int", "min_value": 1, "max_value": 10})
    assert ok
    ok2, _ = validate_data(0, {"type": "int", "min_value": 1})
    assert not ok2


def test_bool_type() -> None:
    """测试 test bool type."""
    ok, _ = validate_data(True, {"type": "bool"})
    assert ok
    ok2, _ = validate_data(1, {"type": "bool"})
    assert not ok2


def test_nested_fields() -> None:
    """测试 test nested fields."""
    schema = {"type": "dict", "fields": {"name": {"type": "str", "min_length": 1}}}
    ok, _ = validate_data({"name": "alice"}, schema)
    assert ok
    ok2, _ = validate_data({"name": ""}, schema)
    assert not ok2


def test_no_type_always_passes() -> None:
    """测试 test no type always passes."""
    ok, _ = validate_data({"anything": True}, {})
    assert ok
