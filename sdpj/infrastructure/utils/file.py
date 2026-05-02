"""UtilsLib 文件处理工具"""
from pathlib import Path


def read_file(file_path: str, mode: str = 'text') -> str | bytes:
    """读取文件"""
    path = Path(file_path)
    if mode == 'text':
        return path.read_text(encoding='utf-8')
    else:
        return path.read_bytes()


def write_file(file_path: str, content: str | bytes, mode: str = 'text') -> bool:
    """写入文件"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if mode == 'text':
        path.write_text(content, encoding='utf-8')
    else:
        path.write_bytes(content)
    return True


def validate_file_format(content: str, format_type: str) -> tuple[bool, str]:
    """文件格式校验"""
    import json

    if format_type == 'json':
        try:
            json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, str(e)

    return True, ""
