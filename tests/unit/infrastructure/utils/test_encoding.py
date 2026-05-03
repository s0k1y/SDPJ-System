import pytest
from sdpj.infrastructure.utils.encoding import (
    base64_encode, base64_decode,
    url_encode, url_decode,
    unicode_escape_encode, unicode_escape_decode,
    hex_encode, hex_decode,
    encode_text, decode_text,
)


def test_base64_roundtrip():
    assert base64_decode(base64_encode("hello")) == "hello"


def test_url_roundtrip():
    assert url_decode(url_encode("hello world")) == "hello world"


def test_unicode_escape_roundtrip():
    assert unicode_escape_decode(unicode_escape_encode("你好")) == "你好"


def test_hex_roundtrip():
    assert hex_decode(hex_encode("abc")) == "abc"


def test_encode_text_dispatch():
    for enc in ("base64", "url", "unicode_escape", "hex"):
        result = encode_text("test", enc)
        assert decode_text(result, enc) == "test"


def test_encode_text_unknown_raises():
    with pytest.raises(KeyError):
        encode_text("test", "unknown")
