"""test_encoding 模块单元测试."""

import pytest
from sdpj.infrastructure.utils.encoding import (
    base64_encode,
    base64_decode,
    url_encode,
    url_decode,
    unicode_escape_encode,
    unicode_escape_decode,
    hex_encode,
    hex_decode,
    encode_text,
    decode_text,
)
from typing import Any


def test_base64_roundtrip() -> None:
    """测试 test base64 roundtrip."""
    assert base64_decode(base64_encode("hello")) == "hello"


def test_url_roundtrip() -> None:
    """测试 test url roundtrip."""
    assert url_decode(url_encode("hello world")) == "hello world"


def test_unicode_escape_roundtrip() -> None:
    """测试 test unicode escape roundtrip."""
    assert unicode_escape_decode(unicode_escape_encode("你好")) == "你好"


def test_hex_roundtrip() -> None:
    """测试 test hex roundtrip."""
    assert hex_decode(hex_encode("abc")) == "abc"


def test_encode_text_dispatch() -> None:
    """测试 test encode text dispatch."""
    for enc in ("base64", "url", "unicode_escape", "hex"):
        result = encode_text("test", enc)
        assert decode_text(result, enc) == "test"


def test_encode_text_unknown_raises() -> None:
    """测试 test encode text unknown raises."""
    with pytest.raises(KeyError):
        encode_text("test", "unknown")


# ===== 多编码间接注入扩展测试 =====

from sdpj.infrastructure.utils.encoding import (
    build_encoded_injection_sample,
    get_encoding_types,
    get_attack_path_label,
    _ENCODING_META,
    _INDUCTION_TEMPLATES,
)

_EXPECTED_ENCODINGS = [
    "base16", "base32", "base64", "base85",
    "rot13", "hex", "morse", "ascii", "unicode",
    "caesar", "vigenere", "url", "unicode_escape",
]


def test_encoding_registry_has_13_encodings() -> None:
    """编码注册表应包含 13 种编码类型。"""
    assert len(_ENCODING_META) == 13
    for name in _EXPECTED_ENCODINGS:
        assert name in _ENCODING_META


def test_encoding_meta_has_chinese_compatible() -> None:
    """每种编码的元数据应包含 chinese_compatible 属性。"""
    for name, meta in _ENCODING_META.items():
        assert "chinese_compatible" in meta, f"{name} missing chinese_compatible"
        assert isinstance(meta["chinese_compatible"], bool)


def test_chinese_incompatible_encodings() -> None:
    """rot13/caesar/vigenere/morse 应标记为不兼容中文。"""
    incompatible = {"rot13", "caesar", "vigenere", "morse"}
    for name in incompatible:
        assert _ENCODING_META[name]["chinese_compatible"] is False


def test_chinese_compatible_encodings() -> None:
    """base64/hex/unicode_escape/url 等应标记为兼容中文。"""
    compatible = {"base64", "base16", "base32", "base85", "hex", "ascii", "unicode", "unicode_escape", "url"}
    for name in compatible:
        assert _ENCODING_META[name]["chinese_compatible"] is True


def test_induction_templates_exist_for_all_encodings() -> None:
    """每种编码应有对应的诱导模板。"""
    for name in _EXPECTED_ENCODINGS:
        assert name in _INDUCTION_TEMPLATES, f"{name} missing induction template"
        assert "{encoded}" in _INDUCTION_TEMPLATES[name], f"{name} template missing {{encoded}} placeholder"


def test_build_encoded_injection_sample_base64() -> None:
    """build_encoded_injection_sample 应返回 诱导模板+编码文本 的完整字符串。"""
    result = build_encoded_injection_sample("hello", "base64")
    assert "Base64" in result
    assert "aGVsbG8=" in result  # base64("hello")
    assert "请解码" in result


def test_build_encoded_injection_sample_returns_string() -> None:
    """build_encoded_injection_sample 返回值应为 str 类型。"""
    result = build_encoded_injection_sample("test", "hex")
    assert isinstance(result, str)


def test_get_encoding_types_returns_list() -> None:
    """get_encoding_types 应返回包含 13 项的列表。"""
    types = get_encoding_types()
    assert isinstance(types, list)
    assert len(types) == 13


def test_get_encoding_types_item_structure() -> None:
    """每个编码类型项应包含 name、label、chinese_compatible 字段。"""
    types = get_encoding_types()
    for item in types:
        assert "name" in item
        assert "label" in item
        assert "chinese_compatible" in item


def test_get_attack_path_label_direct() -> None:
    """encoding_type=None 时应返回 'direct'。"""
    assert get_attack_path_label(None) == "direct"


def test_get_attack_path_label_indirect() -> None:
    """encoding_type 不为 None 时应返回 'indirect:multi-encoding:{encoding}'。"""
    assert get_attack_path_label("base64") == "indirect:multi-encoding:base64"
    assert get_attack_path_label("morse") == "indirect:multi-encoding:morse"


def test_encode_text_still_works_for_all_encodings() -> None:
    """encode_text 应支持全部 13 种编码。"""
    for enc in _EXPECTED_ENCODINGS:
        result = encode_text("hello", enc)
        assert isinstance(result, str)
        assert len(result) > 0
