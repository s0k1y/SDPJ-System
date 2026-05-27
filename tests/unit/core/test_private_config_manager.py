"""test_private_config_manager 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sdpj.core.private_config_manager import PrivateConfigManager
from tests.fixtures.sample_data import REAL_MODEL_ID, REAL_DATASET_SAMPLES, REAL_RISK_TYPE
from typing import Any


def make_manager() -> None:
    """测试 make manager."""
    dp = AsyncMock()
    uc = AsyncMock()
    reg = AsyncMock()
    dp.validate_file_format = MagicMock(return_value=(True, ""))
    dp.serialize_data = MagicMock(return_value='{"key": "val"}')
    dp.deserialize_data = MagicMock(return_value={"key": "val"})
    return PrivateConfigManager(dp, uc, reg), dp, uc, reg


@pytest.mark.asyncio
async def test_create_config_success() -> None:
    """测试 test create config success."""
    mgr, dp, uc, reg = make_manager()
    reg.is_model_available = AsyncMock(return_value=(True, None))
    reg.register_private_model = AsyncMock(return_value=(True, REAL_MODEL_ID, ""))
    uc.register_resource = AsyncMock(return_value=10)
    uc.write_private_config = AsyncMock()
    ok, rid, msg = await mgr.create_config(1, {"model_id": REAL_MODEL_ID, "k": "v"})
    assert ok and rid == 10


@pytest.mark.asyncio
async def test_create_config_model_unavailable() -> None:
    """测试 test create config model unavailable."""
    mgr, dp, uc, reg = make_manager()
    uc.register_resource = AsyncMock(side_effect=ValueError("注册失败"))
    ok, rid, msg = await mgr.create_config(1, {"model_id": "bad-model"})
    assert not ok and rid is None


@pytest.mark.asyncio
async def test_read_config() -> None:
    """测试 test read config."""
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value={"k": "v"})
    result = await mgr.read_config(1)
    assert result == {"k": "v"}


@pytest.mark.asyncio
async def test_delete_config() -> None:
    """测试 test delete config."""
    mgr, dp, uc, reg = make_manager()
    uc.delete_resource = AsyncMock(return_value=True)
    assert await mgr.delete_config(1) is True


@pytest.mark.asyncio
async def test_upload_dataset_success() -> None:
    """测试 test upload dataset success."""
    mgr, dp, uc, reg = make_manager()
    dp.import_private_dataset = AsyncMock(return_value={"dataset_id": 5})
    uc.register_resource = AsyncMock(return_value=20)
    uc.get_user_by_id = AsyncMock(return_value={"username": "testuser"})
    ok, result = await mgr.upload_dataset("ds", REAL_RISK_TYPE, REAL_DATASET_SAMPLES, 1)
    assert ok and result["dataset_id"] == 5


@pytest.mark.asyncio
async def test_upload_dataset_missing_fields() -> None:
    """测试 test upload dataset missing fields."""
    mgr, dp, uc, reg = make_manager()
    ok, result = await mgr.upload_dataset("ds", REAL_RISK_TYPE, [{"poc": "x"}], 1)
    assert not ok and "subtype" in result["error"]


@pytest.mark.asyncio
async def test_remove_dataset() -> None:
    """测试 test remove dataset."""
    mgr, dp, uc, reg = make_manager()
    dp.remove_dataset = AsyncMock(return_value=True)
    uc.delete_resource = AsyncMock(return_value=True)
    assert await mgr.remove_dataset(1, resource_id=5) is True


@pytest.mark.asyncio
async def test_export_config() -> None:
    """测试 test export config."""
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value={"k": "v"})
    result = await mgr.export_config(1, "json")
    assert result == '{"key": "val"}'


@pytest.mark.asyncio
async def test_export_config_not_found() -> None:
    """测试 test export config not found."""
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value=None)
    with pytest.raises(ValueError):
        await mgr.export_config(99, "json")
