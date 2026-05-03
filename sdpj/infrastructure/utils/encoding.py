"""UtilsLib 编码工具"""
import base64
from urllib.parse import quote, unquote


def base64_encode(text: str) -> str:
    """Base64 编码"""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def base64_decode(encoded: str) -> str:
    """Base64 解码"""
    return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')


def url_encode(text: str) -> str:
    """URL 编码"""
    return quote(text)


def url_decode(encoded: str) -> str:
    """URL 解码"""
    return unquote(encoded)


def unicode_escape_encode(text: str) -> str:
    """Unicode 转义编码"""
    return text.encode('unicode_escape').decode('ascii')


def unicode_escape_decode(encoded: str) -> str:
    """Unicode 转义解码"""
    return encoded.encode('ascii').decode('unicode_escape')


def hex_encode(text: str) -> str:
    """十六进制编码"""
    return text.encode('utf-8').hex()


def hex_decode(encoded: str) -> str:
    """十六进制解码"""
    return bytes.fromhex(encoded).decode('utf-8')


_ENCODERS = {"base64": base64_encode, "url": url_encode, "unicode_escape": unicode_escape_encode, "hex": hex_encode}
_DECODERS = {"base64": base64_decode, "url": url_decode, "unicode_escape": unicode_escape_decode, "hex": hex_decode}


def encode_text(text: str, encoding: str) -> str:
    return _ENCODERS[encoding](text)


def decode_text(encoded: str, encoding: str) -> str:
    return _DECODERS[encoding](encoded)
