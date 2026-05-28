"""UtilsLib 接口定义."""

from typing import Any, Protocol


class UtilsInterface(Protocol):  # noqa: D101
    # 编码
    def encode_text(self, text: str, encoding: str) -> str: ...  # noqa: D102
    def decode_text(self, encoded: str, encoding: str) -> str: ...  # noqa: D102

    # 文件 I/O
    def read_file(self, file_path: str, mode: str = "text") -> str | bytes: ...  # noqa: D102
    def write_file(self, file_path: str, content: str | bytes, mode: str = "text") -> bool: ...  # noqa: D102
    def validate_file_format(self, content: str, format_type: str) -> tuple[bool, str]: ...  # noqa: D102

    # 序列化
    def serialize_json(self, obj: Any) -> str: ...  # noqa: ANN401, D102
    def deserialize_json(self, text: str) -> Any: ...  # noqa: ANN401, D102
    def serialize_yaml(self, obj: Any) -> str: ...  # noqa: ANN401, D102
    def deserialize_yaml(self, text: str) -> Any: ...  # noqa: ANN401, D102
