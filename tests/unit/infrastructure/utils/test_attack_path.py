"""attack_path 解析单元测试 (TDD - RED 阶段)."""

from __future__ import annotations

import pytest

from sdpj.infrastructure.utils.attack_path import parse_attack_path


class TestParseAttackPathValid:
    """合法 attack_path 字符串解析."""

    def test_direct(self) -> None:
        """direct 应返回 ('direct', None)."""
        assert parse_attack_path("direct") == ("direct", None)

    @pytest.mark.parametrize(
        "encoding",
        ["base64", "caesar", "hex", "rot13", "morse", "unicode"],
    )
    def test_multi_encoding(self, encoding: str) -> None:
        """indirect:multi-encoding:<编码> 应返回 ('multi-encoding', <编码>)."""
        path = f"indirect:multi-encoding:{encoding}"
        assert parse_attack_path(path) == ("multi-encoding", encoding)

    @pytest.mark.parametrize("modality", ["jpg", "png", "mp3", "wav", "txt", "mhtml"])
    def test_multi_modal(self, modality: str) -> None:
        """indirect:multi-modal:<格式> 应返回 ('multi-modal', <格式>)."""
        path = f"indirect:multi-modal:{modality}"
        assert parse_attack_path(path) == ("multi-modal", modality)


class TestParseAttackPathInvalid:
    """非法 attack_path 字符串应抛 ValueError."""

    def test_empty_string(self) -> None:  # noqa: D102
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("")

    def test_old_format_with_underscore_prefix(self) -> None:
        """旧格式 indirect_multi_encoding:base64 不再被接受."""
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("indirect_multi_encoding:base64")

    def test_unknown_top_level(self) -> None:  # noqa: D102
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("foo")

    def test_missing_detail(self) -> None:  # noqa: D102
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("indirect:multi-encoding")

    def test_unknown_category(self) -> None:  # noqa: D102
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("indirect:unknown-category:base64")

    def test_multi_modal_unsupported_format(self) -> None:
        """multi-modal 仅接受合法格式."""
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("indirect:multi-modal:mp4")

    def test_multi_encoding_unknown_name(self) -> None:  # noqa: D102
        with pytest.raises(ValueError, match="attack_path"):
            parse_attack_path("indirect:multi-encoding:non-existent-encoding")
