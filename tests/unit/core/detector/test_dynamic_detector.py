import pytest
from unittest.mock import AsyncMock, MagicMock
from sdpj.core.sdpj_detector.dynamic_detector import run_dynamic_detection


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    instance = MagicMock()
    llm.get_service_instance = AsyncMock(return_value=instance)
    llm.assemble_request = MagicMock(return_value={})
    llm.invoke_llm = AsyncMock(return_value={"content": "test output"})
    return llm, instance


@pytest.fixture
def mock_data_processor():
    dp = AsyncMock()
    dp.create_task_group = AsyncMock(return_value="dyn_tg_1")
    dp.create_detection_task = AsyncMock(return_value="dyn_task_1")
    dp.create_detection_report = AsyncMock(return_value="dyn_report_1")
    dp.append_result_data = AsyncMock(return_value="result_1")
    dp.update_task_status = AsyncMock()
    return dp


@pytest.mark.asyncio
async def test_dynamic_detection_static_violation_gets_zero_iterations(mock_llm, mock_data_processor):
    """静态就违规的样本，迭代次数应为 0"""
    llm, instance = mock_llm
    dp = mock_data_processor

    # 静态检测结果：一条违规样本
    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["test_poc"],
        "judge_template": "test_template"
    }

    dp.aggregate_task_group_results = AsyncMock(return_value={
        "tasks": [{
            "dataset_id": 1,
            "report": {
                "result_data": [
                    {
                        "risk_subclass": "越狱攻击",
                        "poc": "test_poc",
                        "model_output": "bad output",
                        "compliance_result": "违规"
                    }
                ]
            }
        }]
    })

    result = await run_dynamic_detection(llm, dp, "gpt-4", "user_1", static_result, max_iterations=3)

    assert result["status"] == "completed"
    assert result["task_group_id"] == "dyn_tg_1"

    # 检查 append_result_data 被调用时传入了 iteration_count=0
    dp.append_result_data.assert_called_once()
    call_kwargs = dp.append_result_data.call_args.kwargs
    assert call_kwargs["iteration_count"] == 0


@pytest.mark.asyncio
async def test_dynamic_detection_tracks_iterations(mock_llm, mock_data_processor):
    """动态检测应跟踪每个样本的迭代次数"""
    llm, instance = mock_llm
    dp = mock_data_processor

    # 模拟 LLM 调用：第一次返回合规，第二次返回违规
    call_count = [0]

    async def mock_invoke(inst, req):
        call_count[0] += 1
        if call_count[0] % 4 == 0:  # 每4次调用中的第4次是判断，返回违规
            return {"content": "违规"}
        return {"content": "test output"}

    llm.invoke_llm = AsyncMock(side_effect=mock_invoke)

    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["poc1"],
        "judge_template": "template"
    }

    dp.aggregate_task_group_results = AsyncMock(return_value={
        "tasks": [{
            "dataset_id": 1,
            "report": {
                "result_data": [
                    {
                        "risk_subclass": "越狱攻击",
                        "poc": "original_poc",
                        "model_output": "output",
                        "compliance_result": "合规"
                    }
                ]
            }
        }]
    })

    result = await run_dynamic_detection(llm, dp, "gpt-4", "user_1", static_result, max_iterations=3)

    assert result["status"] == "completed"
    # 应该调用了两次 append_result_data（一次是合规样本的动态检测结果）
    assert dp.append_result_data.call_count >= 1

    # 最后一次调用应该有 iteration_count
    last_call_kwargs = dp.append_result_data.call_args.kwargs
    assert "iteration_count" in last_call_kwargs
    assert last_call_kwargs["iteration_count"] > 0


@pytest.mark.asyncio
async def test_dynamic_detection_avg_iteration_count(mock_llm, mock_data_processor):
    """动态检测应返回平均迭代次数"""
    llm, instance = mock_llm
    dp = mock_data_processor

    static_result = {
        "status": "completed",
        "task_group_id": "static_tg_1",
        "poc_pool": ["poc1"],
        "judge_template": "template"
    }

    # 两个样本：一个静态违规（0次），一个需要迭代
    dp.aggregate_task_group_results = AsyncMock(return_value={
        "tasks": [{
            "dataset_id": 1,
            "report": {
                "result_data": [
                    {"risk_subclass": "A", "poc": "p1", "model_output": "o1", "compliance_result": "违规"},
                    {"risk_subclass": "B", "poc": "p2", "model_output": "o2", "compliance_result": "合规"},
                ]
            }
        }]
    })

    result = await run_dynamic_detection(llm, dp, "gpt-4", "user_1", static_result, max_iterations=3)

    assert "avg_iteration_count" in result
    assert isinstance(result["avg_iteration_count"], float)


@pytest.mark.asyncio
async def test_dynamic_detection_no_static_base():
    """没有静态检测基础时应返回错误状态"""
    llm = AsyncMock()
    dp = AsyncMock()

    static_result = {"status": "no_jailbreak_risk"}

    result = await run_dynamic_detection(llm, dp, "gpt-4", "user_1", static_result, max_iterations=3)

    assert result["status"] == "no_static_base"
    assert result["task_group_id"] is None
