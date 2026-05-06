import pytest
from unittest.mock import AsyncMock, MagicMock
from sdpj.core.private_config_manager import PrivateConfigManager


def make_manager():
    dp = AsyncMock()
    uc = AsyncMock()
    reg = AsyncMock()
    dp.validate_file_format = MagicMock(return_value=(True, ""))
    dp.serialize_data = MagicMock(return_value='{"key": "val"}')
    dp.deserialize_data = MagicMock(return_value={"key": "val"})
    return PrivateConfigManager(dp, uc, reg), dp, uc, reg


@pytest.mark.asyncio
async def test_create_config_success():
    mgr, dp, uc, reg = make_manager()
    reg.is_model_available = AsyncMock(return_value=(True, None))
    uc.register_resource = AsyncMock(return_value=10)
    uc.write_private_config = AsyncMock()
    ok, rid = await mgr.create_config(1, {"model_id": "gpt-4", "k": "v"})
    assert ok and rid == 10


@pytest.mark.asyncio
async def test_create_config_model_unavailable():
    mgr, dp, uc, reg = make_manager()
    uc.register_resource = AsyncMock(side_effect=ValueError("注册失败"))
    ok, rid = await mgr.create_config(1, {"model_id": "bad-model"})
    assert not ok and rid is None


@pytest.mark.asyncio
async def test_read_config():
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value={"k": "v"})
    result = await mgr.read_config(1)
    assert result == {"k": "v"}


@pytest.mark.asyncio
async def test_delete_config():
    mgr, dp, uc, reg = make_manager()
    uc.delete_resource = AsyncMock(return_value=True)
    assert await mgr.delete_config(1) is True


@pytest.mark.asyncio
async def test_upload_dataset_success():
    mgr, dp, uc, reg = make_manager()
    dp.import_private_dataset = AsyncMock(return_value={"dataset_id": 5})
    uc.register_resource = AsyncMock(return_value=20)
    ok, result = await mgr.upload_dataset("ds", "越狱", [{"poc": "x", "subtype": "s"}], 1)
    assert ok and result["dataset_id"] == 5


@pytest.mark.asyncio
async def test_upload_dataset_missing_fields():
    mgr, dp, uc, reg = make_manager()
    ok, result = await mgr.upload_dataset("ds", "越狱", [{"poc": "x"}], 1)
    assert not ok and "subtype" in result["error"]


@pytest.mark.asyncio
async def test_remove_dataset():
    mgr, dp, uc, reg = make_manager()
    dp.remove_dataset = AsyncMock(return_value=True)
    uc.delete_resource = AsyncMock(return_value=True)
    assert await mgr.remove_dataset(1, resource_id=5) is True


@pytest.mark.asyncio
async def test_export_config():
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value={"k": "v"})
    result = await mgr.export_config(1, "json")
    assert result == '{"key": "val"}'


@pytest.mark.asyncio
async def test_export_config_not_found():
    mgr, dp, uc, reg = make_manager()
    uc.read_private_config = AsyncMock(return_value=None)
    with pytest.raises(ValueError):
        await mgr.export_config(99, "json")
