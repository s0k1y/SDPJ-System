from sdpj.infrastructure.utils.validation import validate_data


def test_dict_required_keys_pass():
    ok, _ = validate_data({"a": 1, "b": 2}, {"type": "dict", "required_keys": ["a", "b"]})
    assert ok


def test_dict_missing_required_key():
    ok, msg = validate_data({"a": 1}, {"type": "dict", "required_keys": ["a", "b"]})
    assert not ok and "b" in msg


def test_dict_disallowed_key():
    ok, msg = validate_data({"a": 1, "x": 2}, {"type": "dict", "allowed_keys": ["a"]})
    assert not ok and "x" in msg


def test_list_min_length():
    ok, msg = validate_data([], {"type": "list", "min_length": 1})
    assert not ok


def test_list_values_schema():
    ok, _ = validate_data([1, 2], {"type": "list", "values_schema": {"type": "int"}})
    assert ok
    ok2, _ = validate_data([1, "x"], {"type": "list", "values_schema": {"type": "int"}})
    assert not ok2


def test_str_length():
    ok, _ = validate_data("hi", {"type": "str", "min_length": 2, "max_length": 5})
    assert ok
    ok2, _ = validate_data("h", {"type": "str", "min_length": 2})
    assert not ok2


def test_int_range():
    ok, _ = validate_data(5, {"type": "int", "min_value": 1, "max_value": 10})
    assert ok
    ok2, _ = validate_data(0, {"type": "int", "min_value": 1})
    assert not ok2


def test_bool_type():
    ok, _ = validate_data(True, {"type": "bool"})
    assert ok
    ok2, _ = validate_data(1, {"type": "bool"})
    assert not ok2


def test_nested_fields():
    schema = {"type": "dict", "fields": {"name": {"type": "str", "min_length": 1}}}
    ok, _ = validate_data({"name": "alice"}, schema)
    assert ok
    ok2, _ = validate_data({"name": ""}, schema)
    assert not ok2


def test_no_type_always_passes():
    ok, _ = validate_data({"anything": True}, {})
    assert ok
