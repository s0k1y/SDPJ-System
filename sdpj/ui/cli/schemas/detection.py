"""检测命令输入验证 — 对齐 WebUI schemas/detection.py."""

from __future__ import annotations

from pydantic import BaseModel

from sdpj.infrastructure.utils.attack_path import parse_attack_path


class DetectionStartParams(BaseModel):  # noqa: D101
    model_id: str | int
    detection_type: str = "static"
    dataset_ids: list[int] = []
    jailbreak_dataset_ids: list[int] = []
    config_id: int | None = None
    max_iterations: int = 3
    force_refresh: bool = False
    encoding_types: list[str] = []
    modalities: list[str] = []
    has_direct: bool = True

    @classmethod
    def from_attack_paths(cls, attack_paths: list[str], **kwargs) -> DetectionStartParams:  # noqa: ANN003
        """将 attack_paths 列表转换为 encoding_types + modalities + has_direct.

        attack_paths 格式: ["direct", "indirect:multi-encoding:base64",
        "indirect:multi-modal:png", ...]
        """
        has_direct = False
        encoding_types: list[str] = []
        modalities: list[str] = []

        for raw in attack_paths:
            kind, name = parse_attack_path(raw)
            if kind == "direct":
                has_direct = True
            elif kind == "multi-encoding":
                encoding_types.append(name)  # type: ignore[arg-type]
            elif kind == "multi-modal":
                modalities.append(name)  # type: ignore[arg-type]

        return cls(
            has_direct=has_direct,
            encoding_types=encoding_types,
            modalities=modalities,
            **kwargs,
        )
