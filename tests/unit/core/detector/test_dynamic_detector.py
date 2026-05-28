"""test_dynamic_detector 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sdpj.core.sdpj_detector.dynamic_detector import run_dynamic_detection
from typing import Any


@pytest.fixture
def mock_llm() -> None:
    """测试 mock llm."""
    llm = AsyncMock()
    instance = MagicMock()
    llm.get_service_instance = AsyncMock(return_value=instance)
    llm.assemble_request = MagicMock(return_value={})
    llm.invoke_llm = AsyncMock(return_value={"content": "test output"})
    return llm, instance


@pytest.fixture
def mock_data_processor() -> None:
    """测试 mock data processor."""
    dp = AsyncMock()
    dp.create_task_group = AsyncMock(return_value="dyn_tg_1")
    dp.create_detection_task = AsyncMock(return_value="dyn_task_1")
    dp.create_detection_report = AsyncMock(return_value="dyn_report_1")
    dp.append_result_data = AsyncMock(return_value="result_1")
    dp.append_result_data_batch = AsyncMock(return_value=["result_1"])
    dp.update_task_status = AsyncMock()
    return dp


@pytest.mark.asyncio
async def test_dynamic_detection_static_violation_gets_zero_iterations(
    mock_llm: Any, mock_data_processor: Any
) -> None:
    """静态就违规的样本,迭代次数应为 0"""
    llm, instance = mock_llm
    dp = mock_data_processor

    # 静态检测结果:一条违规样本
    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["test_poc"],
        "judge_template": "test_template",
    }

    dp.aggregate_task_group_results = AsyncMock(
        return_value={
            "tasks": [
                {
                    "dataset_id": 1,
                    "report": {
                        "result_data": [
                            {
                                "risk_subclass": "越狱攻击",
                                "poc": "test_poc",
                                "model_output": "bad output",
                                "compliance_result": "违规",
                            }
                        ]
                    },
                }
            ]
        }
    )

    result = await run_dynamic_detection(
        llm, dp, "gpt-4", "user_1", static_result, max_iterations=3
    )

    assert result["status"] == "completed"
    assert result["task_group_id"] == "static_tg_1"

    # 检查 append_result_data_batch 被调用
    dp.append_result_data_batch.assert_called_once()
    call_args = dp.append_result_data_batch.call_args
    entries = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs["entries"]
    assert any(e.get("iteration_count") == 0 for e in entries)


@pytest.mark.asyncio
async def test_dynamic_detection_tracks_iterations(mock_llm: Any, mock_data_processor: Any) -> None:
    """动态检测应跟踪每个样本的迭代次数"""
    llm, instance = mock_llm
    dp = mock_data_processor

    # 模拟 LLM 调用:每次迭代4次调用(mutation, attack, judge, self-review)
    # 第3次(judge)和第4次(self-review)返回"违规",两者同时违规才最终判定违规
    call_count = [0]

    async def mock_invoke(inst: Any, req: Any) -> None:
        """测试 mock invoke."""
        call_count[0] += 1
        if call_count[0] % 4 in (3, 0):
            return {"content": "违规"}
        return {"content": "test output"}

    llm.invoke_llm = AsyncMock(side_effect=mock_invoke)

    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["poc1"],
        "judge_template": "template",
    }

    dp.aggregate_task_group_results = AsyncMock(
        return_value={
            "tasks": [
                {
                    "dataset_id": 1,
                    "report": {
                        "result_data": [
                            {
                                "risk_subclass": "越狱攻击",
                                "poc": "original_poc",
                                "model_output": "output",
                                "compliance_result": "合规",
                            }
                        ]
                    },
                }
            ]
        }
    )

    result = await run_dynamic_detection(
        llm, dp, "gpt-4", "user_1", static_result, max_iterations=3
    )

    assert result["status"] == "completed"
    # 应该调用了 append_result_data_batch
    assert dp.append_result_data_batch.call_count >= 1

    # 批量结果中应该有 iteration_count > 0 的条目
    call_args = dp.append_result_data_batch.call_args
    entries = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs["entries"]
    assert any(e.get("iteration_count", 0) > 0 for e in entries)


@pytest.mark.asyncio
async def test_dynamic_detection_avg_iteration_count(mock_llm: Any, mock_data_processor: Any) -> None:
    """动态检测应返回平均迭代次数"""
    llm, instance = mock_llm
    dp = mock_data_processor

    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["poc1"],
        "judge_template": "template",
    }

    # 两个样本:一个静态违规(0次),一个需要迭代
    dp.aggregate_task_group_results = AsyncMock(
        return_value={
            "tasks": [
                {
                    "dataset_id": 1,
                    "report": {
                        "result_data": [
                            {
                                "risk_subclass": "A",
                                "poc": "p1",
                                "model_output": "o1",
                                "compliance_result": "违规",
                            },
                            {
                                "risk_subclass": "B",
                                "poc": "p2",
                                "model_output": "o2",
                                "compliance_result": "合规",
                            },
                        ]
                    },
                }
            ]
        }
    )

    result = await run_dynamic_detection(
        llm, dp, "gpt-4", "user_1", static_result, max_iterations=3
    )

    assert "avg_iteration_count" in result
    assert isinstance(result["avg_iteration_count"], float)


@pytest.mark.asyncio
async def test_dynamic_detection_no_static_base() -> None:
    """没有静态检测基础时应返回错误状态"""
    llm = AsyncMock()
    dp = AsyncMock()

    static_result = {"status": "no_jailbreak_risk"}

    result = await run_dynamic_detection(
        llm, dp, "gpt-4", "user_1", static_result, max_iterations=3
    )

    assert result["status"] == "no_static_base"
    assert result["task_group_id"] is None


@pytest.mark.asyncio
async def test_multimodal_red_team_stays_text_only(mock_llm: Any, mock_data_processor: Any) -> None:
    """红队模型输入输出应始终为明文,多模态变换仅在发送给被测 LLM 前执行."""
    llm, instance = mock_llm
    dp = mock_data_processor

    # 红队模型返回明文变异 PoC
    # 多模态路径下每次迭代通过 invoke_llm 的调用:mutation, judge, self-review
    # attack 步骤走 call_multimodal,不经过 invoke_llm
    mutation_count = [0]

    async def mock_invoke(inst: Any, req: Any) -> dict:
        mutation_count[0] += 1
        pos = (mutation_count[0] - 1) % 3
        if pos == 0:
            return {"content": "mutated_poc_text"}
        return {"content": "违规"}

    llm.invoke_llm = AsyncMock(side_effect=mock_invoke)
    llm.call_multimodal = AsyncMock(return_value={"content": "target LLM response"})

    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["test_poc"],
        "judge_template": "template",
    }

    dp.aggregate_task_group_results = AsyncMock(
        return_value={
            "tasks": [
                {
                    "dataset_id": 1,
                    "report": {
                        "result_data": [
                            {
                                "risk_subclass": "越狱攻击",
                                "poc": "original_poc",
                                "model_output": "output",
                                "compliance_result": "合规",
                            }
                        ]
                    },
                }
            ]
        }
    )

    multimodal_content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}]
    dp.build_multimodal_content = AsyncMock(return_value=multimodal_content)

    result = await run_dynamic_detection(
        llm, dp, "gpt-4", "user_1", static_result,
        max_iterations=2, attack_path="indirect:multi-modal:png",
    )

    assert result["status"] == "completed"
    assert llm.invoke_llm.call_count >= 1
    assert llm.call_multimodal.call_count >= 1
    dp.build_multimodal_content.assert_called()
    # 最终落库的 PoC 为明文(非多模态 content 数组)
    dp.append_result_data_batch.assert_called()
    entries = dp.append_result_data_batch.call_args[0][1]
    compliant_entry = next(e for e in entries if e["iteration_count"] > 0)
    assert isinstance(compliant_entry["poc"], str)
    assert compliant_entry["poc"] == "mutated_poc_text"
