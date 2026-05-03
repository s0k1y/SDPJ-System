import pytest
from unittest.mock import AsyncMock
from sdpj.core.report_manager import ReportManager


def make_manager():
    dp = AsyncMock()
    uc = AsyncMock()
    return ReportManager(dp, uc), dp, uc


def make_aggregated(results=None):
    return {
        "user_id": "1",
        "model_id": "gpt-4",
        "tasks": [{"report": {"result_data": results or []}}],
    }


def test_calculate_statistics_empty():
    mgr, _, _ = make_manager()
    s = mgr.calculate_statistics([])
    assert s["total"] == 0 and s["risk_level"] == "N/A"


def test_calculate_statistics_all_compliant():
    mgr, _, _ = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"} for _ in range(10)]
    s = mgr.calculate_statistics(results)
    assert s["compliance_rate"] == 100.0 and s["risk_level"] == "低风险"


def test_calculate_statistics_high_risk():
    mgr, _, _ = make_manager()
    results = [{"compliance_result": "违规", "risk_subclass": "A"} for _ in range(10)]
    s = mgr.calculate_statistics(results)
    assert s["risk_level"] == "高风险"


def test_calculate_statistics_distribution():
    mgr, _, _ = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "A"},
        {"compliance_result": "违规", "risk_subclass": "B"},
    ]
    s = mgr.calculate_statistics(results)
    assert s["risk_distribution"] == {"A": 1, "B": 1}


@pytest.mark.asyncio
async def test_generate_static_report():
    mgr, dp, uc = make_manager()
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    uc.get_user_by_id = AsyncMock(return_value={"username": "alice"})
    report = await mgr.generate_static_report("tg_1")
    assert report["report_type"] == "static"


@pytest.mark.asyncio
async def test_list_reports():
    mgr, dp, uc = make_manager()
    dp.list_task_groups = AsyncMock(return_value=[{"task_group_id": "tg_1"}])
    result = await mgr.list_reports()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_delete_report_by_task_group():
    mgr, dp, uc = make_manager()
    dp.delete_task_group = AsyncMock(return_value=True)
    ok, _ = await mgr.delete_report(task_group_id="tg_1")
    assert ok


@pytest.mark.asyncio
async def test_delete_report_no_target():
    mgr, _, _ = make_manager()
    ok, msg = await mgr.delete_report()
    assert not ok and "必须" in msg


@pytest.mark.asyncio
async def test_prepare_visualization_data():
    mgr, dp, uc = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"}]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert "risk_distribution" in viz and "compliance_ratio" in viz
