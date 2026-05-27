"""检测命令输入验证 — 对齐 WebUI schemas/detection.py."""

from __future__ import annotations

from pydantic import BaseModel

_VALID_MULTI_ENCODING = {
    "base16", "base32", "base64", "base85",
    "rot13", "hex", "morse", "ascii", "unicode",
    "caesar", "vigenere", "url", "unicode_escape",
}

_VALID_MULTI_MODAL: set[str] = set()  # 多模态本期未实现，预留


def parse_attack_path(value: str) -> tuple[str, str | None]:
    """解析 attack-path 值，返回 (类型, 编码/模态名).

    格式:
      direct                          → ("direct", None)
      indirect:multi-encoding:base64  → ("indirect_multi_encoding", "base64")
      indirect:multi-modal:image      → ("indirect_multi_modal", "image")
    """
    if value == "direct":
        return "direct", None

    parts = value.split(":")
    if len(parts) != 3 or parts[0] != "indirect":  # noqa: PLR2004
        raise ValueError(f"无效的 attack-path 格式: {value!r}, 期望 'direct' 或 'indirect:<类型>:<名称>'")

    _, category, name = parts
    if category == "multi-encoding":
        if name not in _VALID_MULTI_ENCODING:
            raise ValueError(f"未知编码类型: {name!r}, 可选: {', '.join(sorted(_VALID_MULTI_ENCODING))}")
        return "indirect_multi_encoding", name
    if category == "multi-modal":
        raise ValueError("多模态注入本期尚未实现")
    raise ValueError(f"未知间接注入类型: {category!r}, 可选: multi-encoding, multi-modal")


def format_attack_path_label(kind: str, name: str | None = None) -> str:
    """将解析结果格式化为攻击路径标签."""
    if kind == "direct":
        return "direct"
    if kind == "indirect_multi_encoding":
        return f"indirect:multi-encoding:{name}"
    if kind == "indirect_multi_modal":
        return f"indirect:multi-modal:{name}"
    return kind


class DetectionStartParams(BaseModel):  # noqa: D101
    model_id: str | int
    detection_type: str = "static"
    dataset_ids: list[int] = []
    jailbreak_dataset_ids: list[int] = []
    config_id: int | None = None
    max_iterations: int = 3
    force_refresh: bool = False
    encoding_types: list[str] = []
    has_direct: bool = True

    @classmethod
    def from_attack_paths(cls, attack_paths: list[str], **kwargs) -> DetectionStartParams:  # noqa: ANN003
        """将 attack_paths 列表转换为 encoding_types + has_direct.

        attack_paths 格式: ["direct", "indirect:multi-encoding:base64", ...]
        """
        has_direct = False
        encoding_types: list[str] = []

        for raw in attack_paths:
            kind, name = parse_attack_path(raw)
            if kind == "direct":
                has_direct = True
            elif kind == "indirect_multi_encoding":
                encoding_types.append(name)  # type: ignore[arg-type]

        return cls(has_direct=has_direct, encoding_types=encoding_types, **kwargs)
