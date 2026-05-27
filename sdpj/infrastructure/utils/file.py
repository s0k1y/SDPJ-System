"""UtilsLib 文件处理工具."""

import csv
import io
import json
from pathlib import Path

from sdpj.infrastructure.utils.exceptions import FileError


def read_file(file_path: str, mode: str = "text") -> str | bytes:
    """读取文件."""
    try:
        path = Path(file_path)
        if mode == "text":
            return path.read_text(encoding="utf-8")
        return path.read_bytes()
    except OSError as e:
        raise FileError(str(e)) from e


def write_file(file_path: str, content: str | bytes, mode: str = "text") -> bool:
    """写入文件."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "text":
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            path.write_text(content, encoding="utf-8")
        else:
            path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return True  # noqa: TRY300
    except OSError as e:
        raise FileError(str(e)) from e


def validate_file_format(content: str, format_type: str) -> tuple[bool, str]:  # noqa: C901, PLR0911
    """文件格式校验,支持 json / csv / jsonl."""
    fmt = format_type.lower()

    if fmt == "json":
        try:
            obj = json.loads(content)
            if not isinstance(obj, (dict, list)):
                return False, f"JSON 顶层类型应为 object 或 array,实际为 {type(obj).__name__}"
            return True, ""  # noqa: TRY300
        except json.JSONDecodeError as e:
            return False, f"JSON 解析失败: {e}"

    if fmt == "csv":
        try:
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            if len(rows) < 1:
                return False, "CSV 文件为空"
            header_len = len(rows[0])
            for i, row in enumerate(rows[1:], start=2):
                if len(row) != header_len:
                    return False, f"CSV 第 {i} 行列数 ({len(row)}) 与表头列数 ({header_len}) 不一致"
            return True, ""  # noqa: TRY300
        except csv.Error as e:
            return False, f"CSV 解析失败: {e}"

    if fmt == "jsonl":
        lines = [line for line in content.splitlines() if line.strip()]
        if not lines:
            return False, "JSONL 文件为空"
        for i, line in enumerate(lines, start=1):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                return False, f"JSONL 第 {i} 行解析失败: {e}"
        return True, ""

    return False, f"不支持的格式类型: {format_type}"
