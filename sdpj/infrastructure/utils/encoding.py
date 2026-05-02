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
