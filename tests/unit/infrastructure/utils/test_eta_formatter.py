import pytest
from sdpj.infrastructure.utils.eta_formatter import format_eta


class TestFormatEta:
    def test_negative_returns_calculating(self):
        assert format_eta(-1) == "计算中..."
        assert format_eta(-0.1) == "计算中..."

    def test_zero_seconds(self):
        assert format_eta(0) == "0秒"

    def test_seconds(self):
        assert format_eta(30) == "30秒"
        assert format_eta(59) == "59秒"

    def test_minutes_and_seconds(self):
        assert format_eta(60) == "1分0秒"
        assert format_eta(90) == "1分30秒"
        assert format_eta(3599) == "59分59秒"

    def test_hours_and_minutes(self):
        assert format_eta(3600) == "1小时0分"
        assert format_eta(5400) == "1小时30分"
        assert format_eta(36000) == "10小时0分"

    def test_fractional_seconds(self):
        assert format_eta(45.7) == "45秒"
        assert format_eta(125.3) == "2分5秒"
