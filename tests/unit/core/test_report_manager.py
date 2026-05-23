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
    dp.list_reports_summary = AsyncMock(
        return_value=[
            {
                "task_group_id": "tg_1",
                "user_id": "1",
                "model_id": "gpt-4",
                "compliance_rate": 80.0,
                "risk_level": "中风险",
                "subtype_compliance": [],
                "status": "completed",
                "children": [],
            }
        ]
    )
    uc.get_user_by_id = AsyncMock(return_value={"username": "alice"})
    result = await mgr.list_reports()
    assert len(result) == 1
    assert result[0]["task_group_id"] == "tg_1"
    assert result[0]["user"]["username"] == "alice"


@pytest.mark.asyncio
async def test_delete_report_by_task_group():
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.delete_task_group = AsyncMock(return_value=True)
    ok, _ = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert ok


@pytest.mark.asyncio
async def test_delete_report_no_target():
    mgr, dp, _ = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value=None)
    ok, msg = await mgr.delete_report()
    assert not ok and "不存在" in msg


@pytest.mark.asyncio
async def test_delete_report_ownership_denied():
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value={"user_id": "2"})
    ok, msg = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert not ok and "权限" in msg


@pytest.mark.asyncio
async def test_delete_report_ownership_allowed():
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.delete_task_group = AsyncMock(return_value=True)
    ok, _ = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert ok


@pytest.mark.asyncio
async def test_prepare_visualization_data():
    mgr, dp, uc = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"}]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert "risk_distribution" in viz and "compliance_ratio" in viz


def test_calculate_statistics_subtype_compliance():
    mgr, _, _ = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "违规", "risk_subclass": "越狱攻击"},
        {"compliance_result": "合规", "risk_subclass": "提示词注入"},
    ]
    s = mgr.calculate_statistics(results)
    assert "subtype_compliance" in s
    assert len(s["subtype_compliance"]) == 2
    jailbreak = next(x for x in s["subtype_compliance"] if x["category"] == "越狱攻击")
    assert jailbreak["total"] == 3
    assert jailbreak["passed"] == 2
    assert jailbreak["failed"] == 1
    assert jailbreak["rate"] == 66.67


@pytest.mark.asyncio
async def test_prepare_visualization_data_with_iteration_count():
    mgr, dp, uc = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "A", "iteration_count": 3},
        {"compliance_result": "违规", "risk_subclass": "B", "iteration_count": 5},
        {"compliance_result": "合规", "risk_subclass": "C", "iteration_count": None},
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert viz["avg_iteration_count"] == 4.0


@pytest.mark.asyncio
async def test_prepare_visualization_data_no_iteration_count():
    mgr, dp, uc = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "A", "iteration_count": None},
        {"compliance_result": "违规", "risk_subclass": "B"},
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert viz["avg_iteration_count"] is None


@pytest.mark.asyncio
async def test_export_report_returns_content():
    mgr, dp, uc = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"}]
    aggregated = make_aggregated(results)
    aggregated["task_group_id"] = "tg_1"
    dp.aggregate_task_group_results = AsyncMock(return_value=aggregated)
    dp.export_report_file = AsyncMock(return_value=("tg_1.jsonl", '{"compliance_result": "合规"}'))
    filename, content = await mgr.export_report("tg_1", "jsonl", user_id=1)
    assert filename == "tg_1.jsonl"
    assert "合规" in content


@pytest.mark.asyncio
async def test_export_report_empty_data():
    mgr, dp, uc = make_manager()
    aggregated = make_aggregated(results=[])
    aggregated["task_group_id"] = "tg_empty"
    dp.aggregate_task_group_results = AsyncMock(return_value=aggregated)
    dp.export_report_file = AsyncMock(return_value=("tg_empty.jsonl", ""))
    filename, content = await mgr.export_report("tg_empty", "jsonl", user_id=1)
    assert filename == "tg_empty.jsonl"
    assert content == ""


@pytest.mark.asyncio
async def test_export_report_with_none_task_group_id_still_proceeds():
    mgr, dp, uc = make_manager()
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.export_report_file = AsyncMock(return_value=("None.jsonl", ""))
    filename, content = await mgr.export_report(None, "jsonl", user_id=1)
    assert dp.aggregate_task_group_results.call_count == 2
    dp.export_report_file.assert_called_once()
