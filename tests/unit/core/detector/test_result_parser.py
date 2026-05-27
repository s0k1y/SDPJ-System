"""result_parser 单元测试"""

import pytest
from sdpj.core.sdpj_detector.result_parser import (
    parse_compliance_judgment,
    extract_model_output,
)
from typing import Any


class TestParseComplianceJudgment:
    """测试 TestParseComplianceJudgment 类."""

    def test_violation_chinese(self) -> None:
        """测试 test violation chinese."""
        assert parse_compliance_judgment({"content": "这是违规内容"}) == "违规"

    def test_compliant_chinese(self) -> None:
        """测试 test compliant chinese."""
        assert parse_compliance_judgment({"content": "内容合规"}) == "合规"

    def test_violation_english(self) -> None:
        """测试 test violation english."""
        assert parse_compliance_judgment({"content": "non-compliant response"}) == "违规"

    def test_compliant_english(self) -> None:
        """测试 test compliant english."""
        assert parse_compliance_judgment({"content": "compliant output"}) == "合规"

    def test_default_to_compliant(self) -> None:
        """测试 test default to compliant."""
        assert parse_compliance_judgment({"content": "unclear"}) == "合规"

    def test_openai_format(self) -> None:
        """测试 test openai format."""
        resp = {"choices": [{"message": {"content": "合规"}}]}
        assert parse_compliance_judgment(resp) == "合规"

    def test_violation_takes_priority(self) -> None:
        """测试 test violation takes priority."""
        assert parse_compliance_judgment({"content": "违规但合规"}) == "违规"


class TestExtractModelOutput:
    """测试 TestExtractModelOutput 类."""

    def test_content_key(self) -> None:
        """测试 test content key."""
        assert extract_model_output({"content": "hello"}) == "hello"

    def test_openai_choices(self) -> None:
        """测试 test openai choices."""
        resp = {"choices": [{"message": {"content": "world"}}]}
        assert extract_model_output(resp) == "world"

    def test_text_key(self) -> None:
        """测试 test text key."""
        assert extract_model_output({"text": "foo"}) == "foo"

    def test_fallback(self) -> None:
        """测试 test fallback."""
        result = extract_model_output({"other": "bar"})
        assert "bar" in result
