import pytest
import tempfile, os
from sdpj.infrastructure.utils.file import read_file, write_file, validate_file_format


def test_write_and_read_text(tmp_path):
    p = str(tmp_path / "f.txt")
    write_file(p, "hello")
    assert read_file(p) == "hello"


def test_write_and_read_binary(tmp_path):
    p = str(tmp_path / "f.bin")
    write_file(p, b"\x00\x01", mode="binary")
    assert read_file(p, mode="binary") == b"\x00\x01"


def test_write_creates_parent_dirs(tmp_path):
    p = str(tmp_path / "a" / "b" / "f.txt")
    write_file(p, "x")
    assert os.path.exists(p)


def test_validate_json_valid():
    ok, _ = validate_file_format('{"a": 1}', "json")
    assert ok


def test_validate_json_invalid():
    ok, msg = validate_file_format("not json", "json")
    assert not ok and msg


def test_validate_yaml_valid():
    ok, msg = validate_file_format("key: value", "yaml")
    assert not ok


def test_validate_yaml_invalid():
    ok, msg = validate_file_format(":\n  bad: [", "yaml")
    assert not ok


def test_validate_csv_valid():
    ok, _ = validate_file_format("a,b\n1,2\n3,4", "csv")
    assert ok


def test_validate_csv_column_mismatch():
    ok, msg = validate_file_format("a,b\n1,2,3", "csv")
    assert not ok


def test_validate_unsupported_format():
    ok, msg = validate_file_format("data", "xml")
    assert not ok
