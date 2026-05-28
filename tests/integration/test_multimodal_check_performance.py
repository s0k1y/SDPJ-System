"""multimodal_check 端点性能基线测试."""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from sdpj.control.state_scheduler import StateScheduler


def _make_scheduler(**overrides):  # noqa: ANN003, ANN202
    config = AsyncMock()
    config.is_model_available = AsyncMock(return_value=(True, MagicMock()))
    config.initialize_registry = AsyncMock(return_value=True)
    config.shutdown_registry = AsyncMock(return_value=True)
    config.register_private_model = AsyncMock(return_value=(True, "m", ""))
    config.read_config = AsyncMock(return_value=None)
    config.query_datasets = AsyncMock(return_value=[])
    defaults = {
        "account_manager": AsyncMock(),
        "dac_manager": AsyncMock(),
        "config_manager": config,
        "report_manager": AsyncMock(),
        "detector": AsyncMock(),
        "event_logger": MagicMock(),
        "task_queue_manager": AsyncMock(),
    }
    defaults.update(overrides)
    return StateScheduler(**defaults)


@pytest.mark.asyncio
class TestMultimodalCheckPerformance:
    """验证 multimodal_check 操作响应耗时 < 100ms."""

    async def test_check_with_cache_under_100ms(self) -> None:
        config = AsyncMock()
        config.read_config = AsyncMock(return_value={
            "multimodal_test_result": {"supported_types": ["image_url", "input_audio"]},
        })
        dac = AsyncMock()
        dac.check_access = AsyncMock(return_value=True)
        s = _make_scheduler(config_manager=config, dac_manager=dac)

        start = time.monotonic()
        result = await s.schedule_config_operation("multimodal_check", {"config_id": 1, "user_id": 1})
        elapsed_ms = (time.monotonic() - start) * 1000

        assert result["success"]
        assert result["result"]["supported_types"] == ["image_url", "input_audio"]
        assert elapsed_ms < 100, f"multimodal_check took {elapsed_ms:.1f}ms, expected < 100ms"

    async def test_check_without_cache_under_100ms(self) -> None:
        config = AsyncMock()
        config.read_config = AsyncMock(return_value={"content": {}})
        dac = AsyncMock()
        dac.check_access = AsyncMock(return_value=True)
        s = _make_scheduler(config_manager=config, dac_manager=dac)

        start = time.monotonic()
        result = await s.schedule_config_operation("multimodal_check", {"config_id": 1, "user_id": 1})
        elapsed_ms = (time.monotonic() - start) * 1000

        assert result["success"]
        assert result["result"]["supported_types"] == []
        assert elapsed_ms < 100, f"multimodal_check took {elapsed_ms:.1f}ms, expected < 100ms"
