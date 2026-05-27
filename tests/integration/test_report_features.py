"""报告功能集成测试 - 子类型合规率和平均迭代次数

测试新增的报告功能:
- subtype_compliance: 按风险子类型统计合规率
- avg_iteration_count: 动态检测平均迭代次数
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from sdpj.core.report_manager import ReportManager


@pytest.fixture
def mock_data_processor():  # noqa: ANN201
    """Mock DataProcessor"""
    dp = AsyncMock()
    return dp


@pytest.fixture
def mock_user_center():  # noqa: ANN201
    """Mock UserCenter"""
    uc = AsyncMock()
    uc.get_user_by_id = AsyncMock(return_value={"user_id": 1, "username": "testuser"})
    return uc


@pytest.fixture
def report_manager(mock_data_processor, mock_user_center):  # noqa: ANN001, ANN201
    """创建 ReportManager 实例"""
    return ReportManager(mock_data_processor, mock_user_center)


class TestSubtypeComplianceIntegration:
    """测试子类型合规率集成"""

    @pytest.mark.asyncio
    async def test_prepare_visualization_includes_subtype_compliance(
        self, report_manager, mock_data_processor  # noqa: ANN001
    ) -> None:
        """测试可视化数据包含子类型合规率"""
        # Mock 聚合数据
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [
                    {
                        "dataset_id": 1,
                        "report": {
                            "result_data": [
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": None,
                                },
                            ]
                        },
                    }
                ],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        # 验证包含 subtype_compliance
        assert "subtype_compliance" in viz_data
        assert isinstance(viz_data["subtype_compliance"], list)
        assert len(viz_data["subtype_compliance"]) == 2

        # 验证越狱攻击统计
        jailbreak = next(x for x in viz_data["subtype_compliance"] if x["category"] == "越狱攻击")
        assert jailbreak["total"] == 3
        assert jailbreak["passed"] == 2
        assert jailbreak["failed"] == 1
        assert jailbreak["rate"] == 66.67

        # 验证提示词注入统计
        injection = next(x for x in viz_data["subtype_compliance"] if x["category"] == "提示词注入")
        assert injection["total"] == 2
        assert injection["passed"] == 1
        assert injection["failed"] == 1
        assert injection["rate"] == 50.0

    @pytest.mark.asyncio
    async def test_subtype_compliance_with_empty_results(self, report_manager, mock_data_processor) -> None:  # noqa: ANN001
        """测试空结果时的子类型合规率"""
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [{"dataset_id": 1, "report": {"result_data": []}}],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        assert "subtype_compliance" in viz_data
        assert viz_data["subtype_compliance"] == []


class TestIterationCountIntegration:
    """测试平均迭代次数集成"""

    @pytest.mark.asyncio
    async def test_prepare_visualization_with_iteration_counts(
        self, report_manager, mock_data_processor  # noqa: ANN001
    ) -> None:
        """测试可视化数据包含平均迭代次数"""
        # Mock 动态检测数据(包含迭代次数)
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [
                    {
                        "dataset_id": 1,
                        "report": {
                            "result_data": [
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": 0,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": 3,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": 5,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": 2,
                                },
                            ]
                        },
                    }
                ],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        # 验证包含 avg_iteration_count
        assert "avg_iteration_count" in viz_data
        assert viz_data["avg_iteration_count"] == 2.5  # (0 + 3 + 5 + 2) / 4

    @pytest.mark.asyncio
    async def test_avg_iteration_count_ignores_null_values(
        self, report_manager, mock_data_processor  # noqa: ANN001
    ) -> None:
        """测试平均迭代次数忽略 NULL 值(静态检测)"""  # noqa: RUF002
        # 混合静态和动态检测结果
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [
                    {
                        "dataset_id": 1,
                        "report": {
                            "result_data": [
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "A",
                                    "iteration_count": None,
                                },  # 静态
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "B",
                                    "iteration_count": 0,
                                },  # 动态-静态违规
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "C",
                                    "iteration_count": 4,
                                },  # 动态-迭代
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "D",
                                    "iteration_count": 2,
                                },  # 动态-迭代
                            ]
                        },
                    }
                ],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        # 只计算非 NULL 的迭代次数
        assert viz_data["avg_iteration_count"] == 2.0  # (0 + 4 + 2) / 3

    @pytest.mark.asyncio
    async def test_avg_iteration_count_none_when_no_dynamic_data(
        self, report_manager, mock_data_processor  # noqa: ANN001
    ) -> None:
        """测试纯静态检测时平均迭代次数为 None"""
        # 纯静态检测结果(所有 iteration_count 为 None)
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [
                    {
                        "dataset_id": 1,
                        "report": {
                            "result_data": [
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "A",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "B",
                                    "iteration_count": None,
                                },
                            ]
                        },
                    }
                ],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        assert viz_data["avg_iteration_count"] is None


class TestReportFeaturesEndToEnd:
    """端到端测试:完整报告生成流程"""  # noqa: RUF002

    @pytest.mark.asyncio
    async def test_complete_report_with_all_features(self, report_manager, mock_data_processor) -> None:  # noqa: ANN001
        """测试完整报告包含所有新功能"""
        # Mock 完整的检测结果
        mock_data_processor.aggregate_task_group_results = AsyncMock(
            return_value={
                "user_id": "1",
                "model_id": "gpt-4",
                "tasks": [
                    {
                        "dataset_id": 1,
                        "report": {
                            "result_data": [
                                # 越狱攻击 - 动态检测
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": 0,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": 3,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "越狱攻击",
                                    "iteration_count": 1,
                                },
                                # 提示词注入 - 动态检测
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": 5,
                                },
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "提示词注入",
                                    "iteration_count": 2,
                                },
                                # 劫持攻击 - 静态检测
                                {
                                    "compliance_result": "合规",
                                    "risk_subclass": "劫持攻击",
                                    "iteration_count": None,
                                },
                                {
                                    "compliance_result": "违规",
                                    "risk_subclass": "劫持攻击",
                                    "iteration_count": None,
                                },
                            ]
                        },
                    }
                ],
            }
        )

        viz_data = await report_manager.prepare_visualization_data("tg_1")

        # 验证基础统计
        assert viz_data["statistics"]["total"] == 7
        assert viz_data["statistics"]["compliant"] == 4
        assert viz_data["statistics"]["non_compliant"] == 3

        # 验证子类型合规率
        assert len(viz_data["subtype_compliance"]) == 3

        jailbreak = next(x for x in viz_data["subtype_compliance"] if x["category"] == "越狱攻击")
        assert jailbreak["total"] == 3
        assert jailbreak["rate"] == 33.33  # 1/3

        injection = next(x for x in viz_data["subtype_compliance"] if x["category"] == "提示词注入")
        assert injection["total"] == 2
        assert injection["rate"] == 100.0  # 2/2

        hijacking = next(x for x in viz_data["subtype_compliance"] if x["category"] == "劫持攻击")
        assert hijacking["total"] == 2
        assert hijacking["rate"] == 50.0  # 1/2

        # 验证平均迭代次数(只计算动态检测的 5 条)
        assert viz_data["avg_iteration_count"] == 2.2  # (0 + 3 + 1 + 5 + 2) / 5

        # 验证其他可视化数据
        assert "risk_distribution" in viz_data
        assert "compliance_ratio" in viz_data
        assert "attack_success_rate" in viz_data


class TestReportManagerCalculateStatistics:
    """测试 ReportManager.calculate_statistics 方法"""

    def test_calculate_statistics_with_subtype_compliance(self, report_manager) -> None:  # noqa: ANN001
        """测试统计计算包含子类型合规率"""
        results = [
            {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
            {"compliance_result": "合规", "risk_subclass": "越狱攻击"},
            {"compliance_result": "违规", "risk_subclass": "越狱攻击"},
            {"compliance_result": "合规", "risk_subclass": "提示词注入"},
            {"compliance_result": "违规", "risk_subclass": "提示词注入"},
            {"compliance_result": "违规", "risk_subclass": "提示词注入"},
        ]

        stats = report_manager.calculate_statistics(results)

        # 验证基础统计
        assert stats["total"] == 6
        assert stats["compliant"] == 3
        assert stats["non_compliant"] == 3
        assert stats["compliance_rate"] == 50.0

        # 验证子类型合规率
        assert "subtype_compliance" in stats
        assert len(stats["subtype_compliance"]) == 2

        jailbreak = next(x for x in stats["subtype_compliance"] if x["category"] == "越狱攻击")
        assert jailbreak["total"] == 3
        assert jailbreak["passed"] == 2
        assert jailbreak["failed"] == 1
        assert jailbreak["rate"] == 66.67

        injection = next(x for x in stats["subtype_compliance"] if x["category"] == "提示词注入")
        assert injection["total"] == 3
        assert injection["passed"] == 1
        assert injection["failed"] == 2
        assert injection["rate"] == 33.33

    def test_calculate_statistics_empty_results(self, report_manager) -> None:  # noqa: ANN001
        """测试空结果的统计计算"""
        stats = report_manager.calculate_statistics([])

        assert stats["total"] == 0
        assert stats["subtype_compliance"] == []
        assert stats["risk_level"] == "N/A"
