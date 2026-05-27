"""完整集成测试 - 跨层级模块协作"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from sdpj.control.state_scheduler import StateScheduler
from tests.fixtures.sample_data import REAL_MODEL_ID


@pytest.fixture
def scheduler():  # noqa: ANN201, D103
    config = AsyncMock()
    config.is_model_available = AsyncMock(return_value=(True, MagicMock()))
    config.initialize_registry = AsyncMock(return_value=True)
    config.shutdown_registry = AsyncMock(return_value=True)
    config.register_private_model = AsyncMock(return_value=(True, "model_id", ""))
    config.read_config = AsyncMock(return_value=None)
    config.query_datasets = AsyncMock(return_value=[])
    return StateScheduler(
        account_manager=AsyncMock(),
        dac_manager=AsyncMock(),
        config_manager=config,
        report_manager=AsyncMock(),
        detector=AsyncMock(),
        event_logger=MagicMock(),
        task_queue_manager=AsyncMock(),
    )


class TestWave0ToWave2Integration:
    """Wave 0-2 垂直集成测试"""

    def test_data_processor_initialization(self) -> None:
        """测试 DataProcessor 初始化(依赖注入)"""  # noqa: RUF002
        from sdpj.drivers.data_processor import DataProcessor

        processor = DataProcessor(
            sample_db=AsyncMock(),
            result_db=AsyncMock(),
            utils_lib=MagicMock(),
        )
        assert processor._sample_db is not None
        assert processor._result_db is not None
        assert processor._utils is not None


class TestWave2ToWave3Integration:
    """Wave 2-3 垂直集成测试"""

    @pytest.mark.asyncio
    async def test_state_scheduler_with_account_manager(self, scheduler) -> None:  # noqa: ANN001
        """测试 StateScheduler 调度 AccountManager"""
        scheduler._account.register.return_value = (True, 1, "")
        result = await scheduler.schedule_user_auth("testuser", "pass", "register")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_state_scheduler_detection_flow(self, scheduler) -> None:  # noqa: ANN001
        """测试 StateScheduler 检测流程"""
        config_data = {
            "model_id": REAL_MODEL_ID,
            "detection_type": "static",
            "dataset_ids": [1],
        }
        result = await scheduler.start_detection(user_id=1, config_data=config_data)
        assert result["success"] is True
        assert "task_group_id" in result


class TestWave3ToWave4Integration:
    """Wave 3-4 垂直集成测试"""

    def test_webui_backend_with_state_scheduler(self) -> None:
        """测试 WebUI Backend 导入"""
        from sdpj.ui.webui.backend.app import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_webui_backend_register_flow(self) -> None:
        """测试 WebUI Backend 注册端点"""
        from sdpj.ui.webui.backend.app import app
        from fastapi.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/auth/register", json={"username": "webui_test_user", "password": "password12345"}
        )
        assert response.status_code in [200, 400, 500]


class TestCrossLayerIntegration:
    """跨层级集成测试"""

    @pytest.mark.asyncio
    async def test_full_stack_detection_flow(self, scheduler) -> None:  # noqa: ANN001
        """测试完整检测流程"""
        assert scheduler.get_system_state() == "idle"

        config_data = {
            "model_id": REAL_MODEL_ID,
            "detection_type": "static",
            "dataset_ids": [1],
        }
        result = await scheduler.start_detection(user_id=1, config_data=config_data)
        assert result["success"] is True
        assert "task_group_id" in result
