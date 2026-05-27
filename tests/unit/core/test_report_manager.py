"""test_report_manager 模块单元测试."""

import pytest
from unittest.mock import AsyncMock
from sdpj.core.report_manager import ReportManager
from typing import Any


def make_manager() -> None:
    """测试 make manager."""
    dp = AsyncMock()
    uc = AsyncMock()
    return ReportManager(dp, uc), dp, uc


def make_aggregated(results: Any=None) -> None:
    """测试 make aggregated."""
    return {
        "user_id": "1",
        "model_id": "gpt-4",
        "tasks": [{"report": {"result_data": results or []}}],
    }


def test_calculate_statistics_empty() -> None:
    """测试 test calculate statistics empty."""
    mgr, _, _ = make_manager()
    s = mgr.calculate_statistics([])
    assert s["total"] == 0 and s["risk_level"] == "N/A"


def test_calculate_statistics_all_compliant() -> None:
    """测试 test calculate statistics all compliant."""
    mgr, _, _ = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"} for _ in range(10)]
    s = mgr.calculate_statistics(results)
    assert s["compliance_rate"] == 100.0 and s["risk_level"] == "低风险"


def test_calculate_statistics_high_risk() -> None:
    """测试 test calculate statistics high risk."""
    mgr, _, _ = make_manager()
    results = [{"compliance_result": "违规", "risk_subclass": "A"} for _ in range(10)]
    s = mgr.calculate_statistics(results)
    assert s["risk_level"] == "高风险"


def test_calculate_statistics_distribution() -> None:
    """测试 test calculate statistics distribution."""
    mgr, _, _ = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "A"},
        {"compliance_result": "违规", "risk_subclass": "B"},
    ]
    s = mgr.calculate_statistics(results)
    assert s["risk_distribution"] == {"A": 1, "B": 1}


@pytest.mark.asyncio
async def test_generate_static_report() -> None:
    """测试 test generate static report."""
    mgr, dp, uc = make_manager()
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    uc.get_user_by_id = AsyncMock(return_value={"username": "alice"})
    report = await mgr.generate_static_report("tg_1")
    assert report["report_type"] == "static"


@pytest.mark.asyncio
async def test_list_reports() -> None:
    """测试 test list reports."""
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
async def test_delete_report_by_task_group() -> None:
    """测试 test delete report by task group."""
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.delete_task_group = AsyncMock(return_value=True)
    ok, _ = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert ok


@pytest.mark.asyncio
async def test_delete_report_no_target() -> None:
    """测试 test delete report no target."""
    mgr, dp, _ = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value=None)
    ok, msg = await mgr.delete_report()
    assert not ok and "不存在" in msg


@pytest.mark.asyncio
async def test_delete_report_ownership_denied() -> None:
    """测试 test delete report ownership denied."""
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value={"user_id": "2"})
    ok, msg = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert not ok and "权限" in msg


@pytest.mark.asyncio
async def test_delete_report_ownership_allowed() -> None:
    """测试 test delete report ownership allowed."""
    mgr, dp, uc = make_manager()
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.delete_task_group = AsyncMock(return_value=True)
    ok, _ = await mgr.delete_report(task_group_id="tg_1", user_id=1)
    assert ok


@pytest.mark.asyncio
async def test_prepare_visualization_data() -> None:
    """测试 test prepare visualization data."""
    mgr, dp, uc = make_manager()
    results = [{"compliance_result": "合规", "risk_subclass": "A"}]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert "risk_distribution" in viz and "compliance_ratio" in viz


def test_calculate_statistics_subtype_compliance() -> None:
    """测试 test calculate statistics subtype compliance."""
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
async def test_prepare_visualization_data_with_iteration_count() -> None:
    """测试 test prepare visualization data with iteration count."""
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
async def test_prepare_visualization_data_no_iteration_count() -> None:
    """测试 test prepare visualization data no iteration count."""
    mgr, dp, uc = make_manager()
    results = [
        {"compliance_result": "合规", "risk_subclass": "A", "iteration_count": None},
        {"compliance_result": "违规", "risk_subclass": "B"},
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated(results))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert viz["avg_iteration_count"] is None


@pytest.mark.asyncio
async def test_export_report_returns_content() -> None:
    """测试 test export report returns content."""
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
async def test_export_report_empty_data() -> None:
    """测试 test export report empty data."""
    mgr, dp, uc = make_manager()
    aggregated = make_aggregated(results=[])
    aggregated["task_group_id"] = "tg_empty"
    dp.aggregate_task_group_results = AsyncMock(return_value=aggregated)
    dp.export_report_file = AsyncMock(return_value=("tg_empty.jsonl", ""))
    filename, content = await mgr.export_report("tg_empty", "jsonl", user_id=1)
    assert filename == "tg_empty.jsonl"
    assert content == ""


@pytest.mark.asyncio
async def test_export_report_with_none_task_group_id_still_proceeds() -> None:
    """测试 test export report with none task group id still proceeds."""
    mgr, dp, uc = make_manager()
    dp.aggregate_task_group_results = AsyncMock(return_value=make_aggregated())
    dp.export_report_file = AsyncMock(return_value=("None.jsonl", ""))
    filename, content = await mgr.export_report(None, "jsonl", user_id=1)
    assert dp.aggregate_task_group_results.call_count == 2
    dp.export_report_file.assert_called_once()


# ===== 多编码间接注入: attack_path 测试 =====


def _make_aggregated_with_tasks(tasks: list[dict]) -> dict:
    """构造含 tasks 列表的 aggregated 数据。"""
    return {
        "user_id": "1",
        "model_id": "gpt-4",
        "tasks": tasks,
    }


@pytest.mark.asyncio
async def test_prepare_visualization_data_returns_attack_path_list() -> None:
    """prepare_visualization_data 应返回 attack_path 列表。"""
    mgr, dp, uc = make_manager()
    tasks = [
        {
            "task_id": "t1", "dataset_id": "ds1",
            "attack_path": "direct",
            "report": {"result_data": [{"compliance_result": "合规", "risk_subclass": "A"}]},
        },
        {
            "task_id": "t2", "dataset_id": "ds1",
            "attack_path": "indirect:multi-encoding:base64",
            "report": {"result_data": [{"compliance_result": "合规", "risk_subclass": "A"}]},
        },
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks(tasks))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert "attack_path" in viz
    assert isinstance(viz["attack_path"], list)
    assert "direct" in viz["attack_path"]
    assert "indirect:multi-encoding:base64" in viz["attack_path"]


@pytest.mark.asyncio
async def test_prepare_visualization_data_attack_path_sorted() -> None:
    """attack_path 列表应为排序后的结果。"""
    mgr, dp, uc = make_manager()
    tasks = [
        {
            "task_id": "t1", "dataset_id": "ds1",
            "attack_path": "indirect:multi-encoding:morse",
            "report": {"result_data": []},
        },
        {
            "task_id": "t2", "dataset_id": "ds1",
            "attack_path": "direct",
            "report": {"result_data": []},
        },
        {
            "task_id": "t3", "dataset_id": "ds1",
            "attack_path": "indirect:multi-encoding:base64",
            "report": {"result_data": []},
        },
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks(tasks))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert viz["attack_path"] == sorted(viz["attack_path"])


@pytest.mark.asyncio
async def test_prepare_visualization_data_no_tasks_returns_empty_attack_path() -> None:
    """无任务时 attack_path 应为空列表。"""
    mgr, dp, uc = make_manager()
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks([]))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert viz["attack_path"] == []


@pytest.mark.asyncio
async def test_prepare_visualization_data_task_without_attack_path_defaults() -> None:
    """task 缺少 attack_path 时应默认为 'direct'。"""
    mgr, dp, uc = make_manager()
    tasks = [
        {
            "task_id": "t1", "dataset_id": "ds1",
            "report": {"result_data": [{"compliance_result": "合规", "risk_subclass": "A"}]},
        },
    ]
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks(tasks))
    viz = await mgr.prepare_visualization_data("tg_1")
    assert "direct" in viz["attack_path"]


@pytest.mark.asyncio
async def test_prepare_task_visualization_data_returns_attack_path() -> None:
    """prepare_task_visualization_data 应返回单个任务的 attack_path。"""
    mgr, dp, uc = make_manager()
    tasks = [
        {
            "task_id": "t1", "dataset_id": "ds1",
            "attack_path": "indirect:multi-encoding:morse",
            "report": {"result_data": [{"compliance_result": "合规", "risk_subclass": "A"}]},
        },
    ]
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks(tasks))
    viz = await mgr.prepare_task_visualization_data("t1")
    assert viz["attack_path"] == "indirect:multi-encoding:morse"


@pytest.mark.asyncio
async def test_prepare_task_visualization_data_defaults_to_direct() -> None:
    """prepare_task_visualization_data 在 task 无 attack_path 时默认返回 'direct'。"""
    mgr, dp, uc = make_manager()
    tasks = [
        {
            "task_id": "t1", "dataset_id": "ds1",
            "report": {"result_data": [{"compliance_result": "合规", "risk_subclass": "A"}]},
        },
    ]
    dp.resolve_task_group_id = AsyncMock(return_value="tg_1")
    dp.aggregate_task_group_results = AsyncMock(return_value=_make_aggregated_with_tasks(tasks))
    viz = await mgr.prepare_task_visualization_data("t1")
    assert viz["attack_path"] == "direct"
