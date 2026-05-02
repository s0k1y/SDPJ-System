"""ResultDB 主实现类单元测试

测试 ResultDB 类实现的所有接口能力。
"""

import pytest
from datetime import datetime
from sdpj.infrastructure.database.result_db import ResultDB, SessionManager


@pytest.fixture
async def result_db():
    """创建测试用的 ResultDB 实例"""
    session_manager = SessionManager("sqlite+aiosqlite:///:memory:", echo=False)
    await session_manager.create_tables()
    db = ResultDB(session_manager)
    yield db
    await session_manager.close()


# ==================== 被测大模型级能力测试 ====================

@pytest.mark.asyncio
async def test_register_target_model(result_db):
    """测试登记被测大模型"""
    result = await result_db.register_target_model("gpt-4")
    assert result is True

    # 幂等操作：重复登记应该成功
    result = await result_db.register_target_model("gpt-4")
    assert result is True


@pytest.mark.asyncio
async def test_get_target_model(result_db):
    """测试查询被测大模型"""
    await result_db.register_target_model("gpt-4")

    model = await result_db.get_target_model("gpt-4")
    assert model is not None
    assert model["model_id"] == "gpt-4"

    # 查询不存在的模型
    model = await result_db.get_target_model("non-existent")
    assert model is None


# ==================== 检测任务组级能力测试 ====================

@pytest.mark.asyncio
async def test_create_task_group(result_db):
    """测试创建检测任务组"""
    await result_db.register_target_model("gpt-4")

    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    assert task_group_id.startswith("tg_")


@pytest.mark.asyncio
async def test_create_task_group_invalid_model(result_db):
    """测试创建任务组时模型不存在"""
    with pytest.raises(ValueError, match="模型ID .* 在被测大模型表中不存在"):
        await result_db.create_task_group("user_001", "non-existent-model")


@pytest.mark.asyncio
async def test_get_task_group(result_db):
    """测试查询单个任务组"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")

    task_group = await result_db.get_task_group(task_group_id)
    assert task_group["task_group_id"] == task_group_id
    assert task_group["user_id"] == "user_001"
    assert task_group["model_id"] == "gpt-4"


@pytest.mark.asyncio
async def test_get_task_group_not_found(result_db):
    """测试查询不存在的任务组"""
    with pytest.raises(ValueError, match="任务组 .* 不存在"):
        await result_db.get_task_group("non-existent")


@pytest.mark.asyncio
async def test_list_task_groups(result_db):
    """测试查询任务组列表"""
    await result_db.register_target_model("gpt-4")
    await result_db.register_target_model("claude-3")

    tg1 = await result_db.create_task_group("user_001", "gpt-4")
    tg2 = await result_db.create_task_group("user_001", "claude-3")
    tg3 = await result_db.create_task_group("user_002", "gpt-4")

    # 查询所有
    all_groups = await result_db.list_task_groups()
    assert len(all_groups) == 3

    # 按用户ID过滤
    user_groups = await result_db.list_task_groups(user_id="user_001")
    assert len(user_groups) == 2

    # 按模型ID过滤
    model_groups = await result_db.list_task_groups(model_id="gpt-4")
    assert len(model_groups) == 2


@pytest.mark.asyncio
async def test_delete_task_group(result_db):
    """测试删除任务组"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")

    result = await result_db.delete_task_group(task_group_id)
    assert result is True

    # 验证已删除
    with pytest.raises(ValueError):
        await result_db.get_task_group(task_group_id)


# ==================== 检测任务级能力测试 ====================

@pytest.mark.asyncio
async def test_create_detection_task(result_db):
    """测试创建检测任务"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")

    start_time = datetime.now()
    task_id = await result_db.create_detection_task(
        task_group_id,
        "dataset_001",
        "running",
        start_time
    )
    assert task_id.startswith("task_")


@pytest.mark.asyncio
async def test_create_detection_task_invalid_group(result_db):
    """测试创建任务时任务组不存在"""
    with pytest.raises(ValueError, match="任务组ID .* 不存在"):
        await result_db.create_detection_task(
            "non-existent",
            "dataset_001",
            "running",
            datetime.now()
        )


@pytest.mark.asyncio
async def test_get_detection_task(result_db):
    """测试查询单个检测任务"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    start_time = datetime.now()
    task_id = await result_db.create_detection_task(
        task_group_id,
        "dataset_001",
        "running",
        start_time
    )

    task = await result_db.get_detection_task(task_id)
    assert task["task_id"] == task_id
    assert task["task_status"] == "running"
    assert task["dataset_id"] == "dataset_001"


@pytest.mark.asyncio
async def test_update_task_status(result_db):
    """测试更新任务状态"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id,
        "dataset_001",
        "running",
        datetime.now()
    )

    end_time = datetime.now()
    result = await result_db.update_task_status(task_id, "completed", end_time)
    assert result is True

    # 验证更新
    task = await result_db.get_detection_task(task_id)
    assert task["task_status"] == "completed"
    assert task["end_time"] == end_time


@pytest.mark.asyncio
async def test_list_tasks_by_group(result_db):
    """测试按任务组查询任务列表"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")

    task1 = await result_db.create_detection_task(
        task_group_id, "dataset_001", "running", datetime.now()
    )
    task2 = await result_db.create_detection_task(
        task_group_id, "dataset_002", "completed", datetime.now()
    )

    tasks = await result_db.list_tasks_by_group(task_group_id)
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_delete_detection_task(result_db):
    """测试删除检测任务"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "running", datetime.now()
    )

    result = await result_db.delete_detection_task(task_id)
    assert result is True

    # 验证已删除
    with pytest.raises(ValueError):
        await result_db.get_detection_task(task_id)


# ==================== 检测报告级能力测试 ====================

@pytest.mark.asyncio
async def test_create_detection_report(result_db):
    """测试创建检测报告"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )

    report_id = await result_db.create_detection_report(task_id)
    assert report_id.startswith("report_")


@pytest.mark.asyncio
async def test_create_detection_report_invalid_task(result_db):
    """测试创建报告时任务不存在"""
    with pytest.raises(ValueError, match="任务ID .* 不存在"):
        await result_db.create_detection_report("non-existent")


@pytest.mark.asyncio
async def test_get_detection_report(result_db):
    """测试查询单份检测报告"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)

    report = await result_db.get_detection_report(report_id)
    assert report["report_id"] == report_id
    assert report["task_id"] == task_id


@pytest.mark.asyncio
async def test_get_report_by_task(result_db):
    """测试按任务ID查询报告"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)

    report = await result_db.get_report_by_task(task_id)
    assert report is not None
    assert report["report_id"] == report_id


@pytest.mark.asyncio
async def test_list_detection_reports(result_db):
    """测试查询报告列表"""
    await result_db.register_target_model("gpt-4")
    tg1 = await result_db.create_task_group("user_001", "gpt-4")
    tg2 = await result_db.create_task_group("user_002", "gpt-4")

    task1 = await result_db.create_detection_task(tg1, "dataset_001", "completed", datetime.now())
    task2 = await result_db.create_detection_task(tg1, "dataset_002", "completed", datetime.now())
    task3 = await result_db.create_detection_task(tg2, "dataset_001", "completed", datetime.now())

    await result_db.create_detection_report(task1)
    await result_db.create_detection_report(task2)
    await result_db.create_detection_report(task3)

    # 查询所有报告
    all_reports = await result_db.list_detection_reports()
    assert len(all_reports) == 3

    # 按任务组过滤
    group_reports = await result_db.list_detection_reports(task_group_id=tg1)
    assert len(group_reports) == 2


@pytest.mark.asyncio
async def test_delete_detection_report(result_db):
    """测试删除检测报告"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)

    result = await result_db.delete_detection_report(report_id)
    assert result is True

    # 验证已删除
    with pytest.raises(ValueError):
        await result_db.get_detection_report(report_id)


# ==================== 检测结果数据级能力测试 ====================

@pytest.mark.asyncio
async def test_append_result_data(result_db):
    """测试追加检测结果数据"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)

    result_data_id = await result_db.append_result_data(
        report_id,
        "prompt_injection",
        "Test output",
        "non_compliant"
    )
    assert result_data_id.startswith("result_")


@pytest.mark.asyncio
async def test_append_result_data_invalid_report(result_db):
    """测试追加结果数据时报告不存在"""
    with pytest.raises(ValueError, match="检测报告ID .* 不存在"):
        await result_db.append_result_data(
            "non-existent",
            "prompt_injection",
            "Test output",
            "non_compliant"
        )


@pytest.mark.asyncio
async def test_list_result_data_by_report(result_db):
    """测试按报告ID查询结果数据"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)

    await result_db.append_result_data(report_id, "prompt_injection", "Output 1", "non_compliant")
    await result_db.append_result_data(report_id, "jailbreak", "Output 2", "compliant")

    result_data_list = await result_db.list_result_data_by_report(report_id)
    assert len(result_data_list) == 2


@pytest.mark.asyncio
async def test_delete_result_data(result_db):
    """测试删除结果数据"""
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)
    result_data_id = await result_db.append_result_data(
        report_id, "prompt_injection", "Output", "non_compliant"
    )

    result = await result_db.delete_result_data(result_data_id)
    assert result is True

    # 验证已删除
    result_data_list = await result_db.list_result_data_by_report(report_id)
    assert len(result_data_list) == 0


# ==================== 级联删除测试 ====================

@pytest.mark.asyncio
async def test_cascade_delete_full_chain(result_db):
    """测试完整的级联删除链"""
    # 创建完整的数据链
    await result_db.register_target_model("gpt-4")
    task_group_id = await result_db.create_task_group("user_001", "gpt-4")
    task_id = await result_db.create_detection_task(
        task_group_id, "dataset_001", "completed", datetime.now()
    )
    report_id = await result_db.create_detection_report(task_id)
    result_data_id = await result_db.append_result_data(
        report_id, "prompt_injection", "Output", "non_compliant"
    )

    # 删除任务组，应该级联删除所有相关数据
    await result_db.delete_task_group(task_group_id)

    # 验证所有数据都已删除
    with pytest.raises(ValueError):
        await result_db.get_task_group(task_group_id)

    with pytest.raises(ValueError):
        await result_db.get_detection_task(task_id)

    with pytest.raises(ValueError):
        await result_db.get_detection_report(report_id)

    result_data_list = await result_db.list_result_data_by_report(report_id)
    assert len(result_data_list) == 0
