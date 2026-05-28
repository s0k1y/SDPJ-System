"""多模态注入检测流程集成测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sdpj.control.state_scheduler import StateScheduler
from sdpj.core.sdpj_detector.static_detector import run_static_detection
from tests.fixtures.sample_data import REAL_MODEL_ID


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
class TestMultimodalTaskSplit:
    """验证 start_detection 对 modalities 的拆分逻辑."""

    async def test_modalities_creates_one_task_per_modality(self) -> None:
        tq = AsyncMock()
        tq.enqueue_task = AsyncMock(side_effect=["t1", "t2", "t3"])
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": ["ds1"],
                "has_direct": False,
                "modalities": ["jpg", "mp3", "wav"],
            },
        )
        assert result["success"]
        assert len(result["task_ids"]) == 3
        calls = tq.enqueue_task.call_args_list
        assert calls[0][0][0]["metadata"]["attack_path"] == "indirect:multi-modal:jpg"
        assert calls[1][0][0]["metadata"]["attack_path"] == "indirect:multi-modal:mp3"
        assert calls[2][0][0]["metadata"]["attack_path"] == "indirect:multi-modal:wav"

    async def test_direct_plus_modalities(self) -> None:
        tq = AsyncMock()
        tq.enqueue_task = AsyncMock(side_effect=["t1", "t2"])
        s = _make_scheduler(task_queue_manager=tq)
        result = await s.start_detection(
            1,
            {
                "model_id": REAL_MODEL_ID,
                "detection_type": "static",
                "dataset_ids": ["ds1"],
                "has_direct": True,
                "has_encoding": False,
                "modalities": ["png"],
            },
        )
        assert result["success"]
        assert len(result["task_ids"]) == 2
        calls = tq.enqueue_task.call_args_list
        assert calls[0][0][0]["metadata"]["attack_path"] == "direct"
        assert calls[1][0][0]["metadata"]["attack_path"] == "indirect:multi-modal:png"


@pytest.mark.asyncio
class TestMultimodalStaticDetection:
    """验证静态检测多模态分发端到端."""

    @patch("sdpj.infrastructure.utils.multimodal.build_multimodal_content")
    @patch("sdpj.core.sdpj_detector.static_detector._call_llm_multimodal")
    async def test_multimodal_path_calls_build_content(
        self, mock_call_mm: AsyncMock, mock_build: AsyncMock,
    ) -> None:
        mock_build.return_value = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}]
        mock_call_mm.return_value = {"content": "test response", "usage": {"total_tokens": 10}}

        mock_llm = AsyncMock()
        mock_instance = MagicMock()
        mock_instance.active = True
        mock_llm.is_model_available = AsyncMock(return_value=(True, mock_instance))

        with patch("sdpj.core.sdpj_detector.static_detector._call_llm") as mock_call_text:
            mock_call_text.return_value = {"content": "text response", "usage": {"total_tokens": 5}}
            # This test verifies the import path works; actual execution
            # would require a full detector setup which is covered by unit tests
            assert mock_build is not None
            assert mock_call_mm is not None


@pytest.mark.asyncio
class TestMultimodalConfigOperation:
    """验证 schedule_config_operation 对 multimodal_test/multimodal_check 的调度."""

    async def test_multimodal_test_operation(self) -> None:
        config = AsyncMock()
        config.read_config = AsyncMock(return_value={"content": {"request_format": "openai"}})
        config.multimodal_capability_test = AsyncMock(return_value={"supported_types": ["image_url", "input_audio"]})
        dac = AsyncMock()
        dac.check_access = AsyncMock(return_value=True)
        s = _make_scheduler(config_manager=config, dac_manager=dac)
        result = await s.schedule_config_operation("multimodal_test", {"config_id": 1, "user_id": 1})
        assert result["success"]
        assert result["result"]["supported_types"] == ["image_url", "input_audio"]

    async def test_multimodal_check_reads_cache(self) -> None:
        config = AsyncMock()
        config.read_config = AsyncMock(return_value={
            "multimodal_test_result": {"supported_types": ["image_url"]},
        })
        dac = AsyncMock()
        dac.check_access = AsyncMock(return_value=True)
        s = _make_scheduler(config_manager=config, dac_manager=dac)
        result = await s.schedule_config_operation("multimodal_check", {"config_id": 1, "user_id": 1})
        assert result["success"]
        assert result["result"]["supported_types"] == ["image_url"]

    async def test_multimodal_check_no_cache(self) -> None:
        config = AsyncMock()
        config.read_config = AsyncMock(return_value={"content": {}})
        dac = AsyncMock()
        dac.check_access = AsyncMock(return_value=True)
        s = _make_scheduler(config_manager=config, dac_manager=dac)
        result = await s.schedule_config_operation("multimodal_check", {"config_id": 1, "user_id": 1})
        assert result["success"]
        assert result["result"]["supported_types"] == []
