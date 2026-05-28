"""攻击路径(attack_path)结构化字符串解析.

attack_path 是 SDPJDetector / WebUI / CLI 通用的攻击路径鉴别器,格式为:
    direct                              → 直接注入(明文 PoC)
    indirect:multi-encoding:<编码>       → 多编码间接注入(如 base64, caesar)
    indirect:multi-modal:<格式>          → 多模态间接注入(jpg/png/mp3/wav)

本模块只做格式解析与合法性校验,不依赖任何上层模块,供基础设施层、抽象驱动层、
执行逻辑层共同引用.
"""

from __future__ import annotations

from sdpj.infrastructure.utils.encoding import get_encoding_types

VALID_MULTIMODAL_FORMATS: frozenset[str] = frozenset({"jpg", "png", "mp3", "wav"})


def _valid_encoding_names() -> frozenset[str]:
    return frozenset(item["name"] for item in get_encoding_types())


def parse_attack_path(attack_path: str) -> tuple[str, str | None]:
    """解析 attack_path 字符串.

    Args:
        attack_path: 攻击路径字符串.

    Returns:
        ``(path_type, detail)`` 元组:
            ``("direct", None)``、``("multi-encoding", <编码>)`` 或
            ``("multi-modal", <格式>)``.

    Raises:
        ValueError: 字符串格式非法或编码/模态名不在白名单内.

    """
    if attack_path == "direct":
        return "direct", None

    parts = attack_path.split(":")
    if len(parts) != 3 or parts[0] != "indirect":  # noqa: PLR2004
        raise ValueError(
            f"无效的 attack_path: {attack_path!r}, "
            "期望 'direct' 或 'indirect:multi-encoding:<编码>' 或 'indirect:multi-modal:<格式>'",
        )

    _, category, detail = parts

    if category == "multi-encoding":
        valid = _valid_encoding_names()
        if detail not in valid:
            raise ValueError(
                f"未知编码类型 attack_path: {detail!r}, 可选: {', '.join(sorted(valid))}",
            )
        return "multi-encoding", detail

    if category == "multi-modal":
        if detail not in VALID_MULTIMODAL_FORMATS:
            raise ValueError(
                f"未知模态 attack_path: {detail!r}, "
                f"可选: {', '.join(sorted(VALID_MULTIMODAL_FORMATS))}",
            )
        return "multi-modal", detail

    raise ValueError(
        f"未知 attack_path 类型: {category!r}, 可选: multi-encoding, multi-modal",
    )
