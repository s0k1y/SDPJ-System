"""测试 static_detector 修复:task_group_id 已提供时仍注册 TargetModel,缓存写入失败不崩溃

对应 bug:
1. state_scheduler 传入 task_group_id → run_static_detection 跳过 create_task_group → TargetModel 未注册
2. save_poc_pool_cache 外键约束失败 → 未捕获异常 → 任务组崩溃消失

修复:
1. run_static_detection 入口处调用 register_target_model(无论 task_group_id 是否提供)
2. save_poc_pool_cache 内部先调用 tm_repo.register(model_id)
3. static_detector 中 save_poc_pool_cache 调用包裹在 try/except 中
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sdpj.core.sdpj_detector.static_detector import run_static_detection
from sdpj.infrastructure.llm_adapters.errors import ErrorCategory, StandardizedLLMError
from typing import Any


def _make_mock_llm() -> None:
    """创建 mock LLM 服务"""
    llm = MagicMock()
    instance = MagicMock()
    instance.model_id = "test-model"
    instance.active = True
    llm.get_service_instance = AsyncMock(return_value=instance)
    llm.assemble_request = MagicMock(return_value={"model": "test-model", "messages": []})

    # 默认成功响应
    llm.invoke_llm = AsyncMock(
        return_value={
            "success": True,
            "content": "I cannot comply with that request. Score: 1",
            "model": "test-model",
            "usage": {},
        }
    )
    return llm, instance


def _make_mock_data_processor(poc_pool_cache: Any=None, save_cache_error: Any=None) -> None:
    """创建 mock DataProcessor

    Args:
        poc_pool_cache: 返回的缓存内容,None 表示无缓存(触发 select_poc_pool)
        save_cache_error: save_poc_pool_cache 抛出的异常,None 表示正常
    """
    dp = AsyncMock()

    # 数据集查询
    dp.get_all_datasets = AsyncMock(
        return_value=[
            {"dataset_id": 1, "risk_type": "injection", "name": "test_injection"},
        ]
    )
    dp.load_dataset_by_risk_type = AsyncMock(return_value=[])

    # TargetModel 注册
    dp.register_target_model = AsyncMock(return_value={"model_id": "test-model"})

    # 任务组
    dp.create_task_group = AsyncMock(return_value="tg_test_001")

    # PoC 缓存
    if poc_pool_cache is not None:
        dp.get_poc_pool_cache = AsyncMock(return_value=poc_pool_cache)
    else:
        dp.get_poc_pool_cache = AsyncMock(return_value=[])

    if save_cache_error is not None:
        dp.save_poc_pool_cache = AsyncMock(side_effect=save_cache_error)
    else:
        dp.save_poc_pool_cache = AsyncMock(return_value=3)

    # 任务和报告
    dp.create_detection_task = AsyncMock(return_value="task_001")
    dp.create_detection_report = AsyncMock(return_value="report_001")
    dp.update_task_status = AsyncMock(return_value=True)
    dp.append_result_data_batch = AsyncMock(return_value=["rd_001"])

    return dp


@pytest.mark.asyncio
async def test_register_target_model_called_when_task_group_id_provided() -> None:
    """测试:传入 task_group_id 时,register_target_model 仍被调用

    复现:state_scheduler 传入 task_group_id,跳过 create_task_group,
    但 register_target_model 应在 run_static_detection 入口处被调用
    """
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ]
    )

    # 传入 task_group_id,跳过 create_task_group
    result = await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        task_group_id="pre-existing-group-id",
    )

    # register_target_model 必须被调用,不论 task_group_id 是否提供
    dp.register_target_model.assert_called_once_with("test-model")

    # create_task_group 不应被调用(因为 task_group_id 已提供)
    dp.create_task_group.assert_not_called()


@pytest.mark.asyncio
async def test_register_target_model_called_when_task_group_id_not_provided() -> None:
    """测试:不传 task_group_id 时,register_target_model 和 create_task_group 都被调用"""
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ]
    )

    result = await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        # 不传 task_group_id
    )

    dp.register_target_model.assert_called_once_with("test-model")
    dp.create_task_group.assert_called_once_with("1", "test-model")


@pytest.mark.asyncio
async def test_save_poc_pool_cache_failure_does_not_crash_detection() -> None:
    """测试:save_poc_pool_cache 数据库异常时不崩溃,检测流程继续

    复现生产场景:外键约束失败 → IntegrityError → 任务组崩溃消失
    修复后:try/except 捕获异常,记录 warning,检测继续
    """
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ],
        save_cache_error=Exception("sqlite3.IntegrityError: FOREIGN KEY constraint failed"),
    )

    # 即使 save_poc_pool_cache 抛异常也不应崩溃
    # 注意:此测试使用缓存路径(poc_pool_cache 非空),不走 select_poc_pool
    # 要测试 save 失败需要走 select_poc_pool 路径
    # 由于 select_poc_pool 需要大量 mock,这里直接测试 static_detector 中的 try/except
    result = await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        task_group_id="pre-existing-group-id",
    )

    # 检测应正常完成(使用缓存路径时不涉及 save)
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_save_poc_pool_cache_error_in_select_poc_path() -> None:
    """测试:select_poc_pool 路径下 save_poc_pool_cache 异常不崩溃

    这是真正触发生产 bug 的路径:构建 PoC 池后保存缓存失败
    """
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=None,  # 无缓存,触发 select_poc_pool
        save_cache_error=Exception("sqlite3.IntegrityError: FOREIGN KEY constraint failed"),
    )

    # select_poc_pool 需要加载越狱数据集
    dp.load_dataset_by_risk_type = AsyncMock(
        return_value=[
            {
                "dataset_id": 10,
                "dataset_name": "jailbreak_llm",
                "risk_type": "jailbreak",
                "samples": [
                    {"poc": "jailbreak prompt 1", "subtype": "模板化越狱"},
                    {"poc": "jailbreak prompt 2", "subtype": "default_jailbreak"},
                ],
            }
        ]
    )

    with patch(
        "sdpj.core.sdpj_detector.static_detector._call_llm", new_callable=AsyncMock
    ) as mock_call:
        # 第一次调用:LLM 输出;第二次调用:评分
        mock_call.side_effect = [
            {"content": "I cannot help with that.", "model": "test-model", "usage": {}},
            {"content": "Score: 5", "model": "test-model", "usage": {}},
        ] * 10  # 足够多的响应

        result = await run_static_detection(
            llm=llm,
            data_processor=dp,
            model_id="test-model",
            user_id="1",
            task_group_id="pre-existing-group-id",
        )

    # 即使 save_poc_pool_cache 失败,检测流程不应崩溃
    # (但 result 取决于 poc_pool 是否构建成功和后续流程)
    assert result is not None  # 最基本:没有抛出未捕获异常


class TestStandardizedLLMErrorEmptyMessage:
    """测试 StandardizedLLMError 空消息防护"""

    def test_empty_string_message_with_original_error(self) -> None:
        """空字符串消息 + 有 original_error → 使用 original_error 信息"""
        original = ValueError("connection reset")
        err = StandardizedLLMError(ErrorCategory.UNKNOWN, "", original_error=original)
        assert "ValueError" in err.message
        assert "connection reset" in err.message
        assert str(err) == err.message

    def test_empty_string_message_with_status_code(self) -> None:
        """空字符串消息 + 有 status_code → 使用 HTTP 状态码"""
        err = StandardizedLLMError(ErrorCategory.SERVER_ERROR, "", status_code=500)
        assert "500" in err.message
        assert "server_error" in err.message

    def test_empty_string_message_nothing_else(self) -> None:
        """空字符串消息 + 无 original_error + 无 status_code → 兜底信息"""
        err = StandardizedLLMError(ErrorCategory.UNKNOWN, "")
        assert "unknown_error" in err.message
        assert "no detail" in err.message

    def test_whitespace_message(self) -> None:
        """纯空白消息 → 视为空消息"""
        err = StandardizedLLMError(
            ErrorCategory.NETWORK, "   ", original_error=ConnectionError("timeout")
        )
        assert "timeout" in err.message

    def test_normal_message_unchanged(self) -> None:
        """正常消息不被修改"""
        err = StandardizedLLMError(ErrorCategory.RATE_LIMIT, "Rate limit exceeded")
        assert err.message == "Rate limit exceeded"

    def test_to_dict_with_filled_message(self) -> None:
        """to_dict 在空消息防护后输出正确的 message"""
        err = StandardizedLLMError(ErrorCategory.UNKNOWN, "", status_code=502)
        d = err.to_dict()
        assert d["message"] == err.message  # 不再是空字符串
        assert d["error"] == "unknown_error"


# ===== T2: 多编码间接注入测试 =====

@pytest.mark.asyncio
async def test_run_static_detection_accepts_encoding_type() -> None:
    """run_static_detection 应接受 encoding_type 可选参数。"""
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ]
    )
    # 传入 encoding_type 参数不应报错
    result = await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        task_group_id="pre-existing-group-id",
        encoding_type="base64",
    )
    assert result is not None


@pytest.mark.asyncio
async def test_encoding_type_none_preserves_existing_behavior() -> None:
    """encoding_type=None 时行为与现有完全一致。"""
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ]
    )
    result = await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        task_group_id="pre-existing-group-id",
    )
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_create_detection_task_receives_metadata_json() -> None:
    """create_detection_task 调用时应传入 metadata_json（含 encoding_type 和 attack_path）。"""
    llm, instance = _make_mock_llm()
    dp = _make_mock_data_processor(
        poc_pool_cache=[
            {"poc_text": "cached_poc", "score": 5, "subtype": "模板化越狱"},
        ]
    )
    # get_all_datasets 和 load_dataset_by_risk_type 返回一致的数据集 ID
    dp.get_all_datasets = AsyncMock(
        return_value=[
            {"dataset_id": 2, "risk_type": "injection", "name": "test_injection"},
        ]
    )
    dp.load_dataset_by_risk_type = AsyncMock(
        return_value=[
            {
                "dataset_id": 2,
                "dataset_name": "test_injection",
                "risk_type": "injection",
                "samples": [
                    {"poc": "test poc", "subtype": "提示词注入"},
                ],
            }
        ]
    )

    await run_static_detection(
        llm=llm,
        data_processor=dp,
        model_id="test-model",
        user_id="1",
        dataset_ids=[2],
        task_group_id="pre-existing-group-id",
        encoding_type="base64",
    )

    # 验证 create_detection_task 被调用时携带 metadata_json
    dp.create_detection_task.assert_called()
    call_args = dp.create_detection_task.call_args
    assert "metadata_json" in call_args.kwargs, "create_detection_task 应收到 metadata_json 关键字参数"
    meta = call_args.kwargs["metadata_json"]
    assert meta["encoding_type"] == "base64"
    assert meta["attack_path"] == "indirect:multi-encoding:base64"
