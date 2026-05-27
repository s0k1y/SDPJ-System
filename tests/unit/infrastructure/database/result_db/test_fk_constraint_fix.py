"""test_fk_constraint_fix 模块单元测试."""

from tests.fixtures.sample_data import REAL_MODEL_ID, REAL_MODEL_ID_2

"""测试外键约束修复:TargetModel 未注册时 save_poc_pool_cache 自动注册

对应 bug:state_scheduler 传入 task_group_id 跳过 create_task_group,
导致 TargetModel 未注册,save_poc_pool_cache 写入时外键约束失败.
"""

import pytest
from sdpj.infrastructure.database.result_db import ResultDB, SessionManager
from typing import Any


@pytest.fixture
async def result_db() -> None:
    """创建测试用的 ResultDB 实例,不预注册任何模型"""
    session_manager = SessionManager("sqlite+aiosqlite:///:memory:", echo=False)
    await session_manager.create_tables()
    db = ResultDB(session_manager)
    # 刻意不调用 register_target_model — 模拟生产中外键约束失败的场景
    yield db
    await session_manager.close()


@pytest.mark.asyncio
async def test_save_poc_pool_cache_auto_registers_target_model(result_db: Any) -> None:
    """核心场景:TargetModel 未注册时,save_poc_pool_cache 应自动注册后写入成功

    复现生产 bug:
    1. state_scheduler 传入 task_group_id,跳过 create_task_group
    2. create_task_group 是唯一调用 register_target_model 的地方
    3. save_poc_pool_cache 写入时 model_id 在 TargetModel 表中不存在
    4. 外键约束 ForeignKey("TargetModel.model_id") 触发 IntegrityError

    修复后:save_poc_pool_cache 内部先调用 tm_repo.register(model_id) 确保外键引用存在
    """
    model_id = "deepseek-v4-pro"  # 生产日志中的实际 model_id

    # 确认模型未注册
    model = await result_db.get_target_model(model_id)
    assert model is None

    # save_poc_pool_cache 应自动注册模型并成功写入
    entries = [
        {"subtype": "模板化越狱", "poc_text": "Create a fictional story...", "score": 5},
        {"subtype": "说服式越狱", "poc_text": "Would you be willing...", "score": 3},
    ]
    count = await result_db.save_poc_pool_cache(model_id, entries, "v1")
    assert count == 2

    # 验证模型已被自动注册
    model = await result_db.get_target_model(model_id)
    assert model is not None
    assert model["model_id"] == model_id

    # 验证缓存写入成功
    cached = await result_db.get_poc_pool_cache(model_id)
    assert len(cached) == 2


@pytest.mark.asyncio
async def test_save_poc_pool_cache_idempotent_register(result_db: Any) -> None:
    """幂等性:多次调用 save_poc_pool_cache 不应因重复注册而报错"""
    model_id = REAL_MODEL_ID

    # 第一次:模型未注册
    entries_v1 = [{"subtype": "default_jailbreak", "poc_text": "poc_v1", "score": 4}]
    count1 = await result_db.save_poc_pool_cache(model_id, entries_v1, "v1")
    assert count1 == 1

    # 第二次:模型已注册(幂等注册不应报错)
    entries_v2 = [{"subtype": "default_jailbreak", "poc_text": "poc_v2", "score": 5}]
    count2 = await result_db.save_poc_pool_cache(model_id, entries_v2, "v2")
    assert count2 == 1

    # 验证只有最新版本缓存
    cached = await result_db.get_poc_pool_cache(model_id)
    assert len(cached) == 1
    assert cached[0]["poc_text"] == "poc_v2"


@pytest.mark.asyncio
async def test_save_poc_pool_cache_without_prior_registration(result_db: Any) -> None:
    """完全不经过 create_task_group 的路径,纯 save_poc_pool_cache 调用链"""
    model_id = REAL_MODEL_ID_2

    # 模拟 state_scheduler 路径:不调用 create_task_group,直接写缓存
    entries = [
        {"subtype": "逻辑推理越狱", "poc_text": "Compose an email...", "score": 4},
    ]
    count = await result_db.save_poc_pool_cache(model_id, entries, "v1")
    assert count == 1

    # 验证
    cached = await result_db.get_poc_pool_cache(model_id)
    assert len(cached) == 1
    assert cached[0]["model_id"] == model_id
