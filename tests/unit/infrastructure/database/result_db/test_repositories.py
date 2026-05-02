"""ResultDB 仓储层单元测试

测试所有仓储类的数据访问操作。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sdpj.infrastructure.database.result_db.models import Base, TargetModel, TaskGroup, DetectionTask
from sdpj.infrastructure.database.result_db.repositories import (
    TargetModelRepository,
    TaskGroupRepository,
    TaskRepository,
    ReportRepository,
    ResultDataRepository,
)


@pytest.fixture
async def async_session():
    """创建测试用的异步数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# ==================== TargetModelRepository 测试 ====================

@pytest.mark.asyncio
async def test_target_model_repo_create(async_session):
    """测试创建被测大模型"""
    repo = TargetModelRepository(async_session)
    model = await repo.create("gpt-4")

    assert model.model_id == "gpt-4"


@pytest.mark.asyncio
async def test_target_model_repo_get_by_id(async_session):
    """测试按ID查询被测大模型"""
    repo = TargetModelRepository(async_session)
    await repo.create("gpt-4")

    model = await repo.get_by_id("gpt-4")
    assert model is not None
    assert model.model_id == "gpt-4"

    # 查询不存在的模型
    model = await repo.get_by_id("non-existent")
    assert model is None


@pytest.mark.asyncio
async def test_target_model_repo_exists(async_session):
    """测试检查模型是否存在"""
    repo = TargetModelRepository(async_session)
    await repo.create("gpt-4")

    assert await repo.exists("gpt-4") is True
    assert await repo.exists("non-existent") is False


# ==================== TaskGroupRepository 测试 ====================

@pytest.mark.asyncio
async def test_task_group_repo_create(async_session):
    """测试创建任务组"""
    # 先创建被测大模型
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    # 创建任务组
    repo = TaskGroupRepository(async_session)
    task_group = await repo.create("tg_001", "user_001", "gpt-4")

    assert task_group.task_group_id == "tg_001"
    assert task_group.user_id == "user_001"
    assert task_group.model_id == "gpt-4"


@pytest.mark.asyncio
async def test_task_group_repo_get_by_id(async_session):
    """测试按ID查询任务组"""
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    repo = TaskGroupRepository(async_session)
    await repo.create("tg_001", "user_001", "gpt-4")

    task_group = await repo.get_by_id("tg_001")
    assert task_group is not None
    assert task_group.task_group_id == "tg_001"


@pytest.mark.asyncio
async def test_task_group_repo_list_all(async_session):
    """测试查询任务组列表"""
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")
    await model_repo.create("claude-3")

    repo = TaskGroupRepository(async_session)
    await repo.create("tg_001", "user_001", "gpt-4")
    await repo.create("tg_002", "user_001", "claude-3")
    await repo.create("tg_003", "user_002", "gpt-4")

    # 查询所有
    all_groups = await repo.list_all()
    assert len(all_groups) == 3

    # 按用户ID过滤
    user_groups = await repo.list_all(user_id="user_001")
    assert len(user_groups) == 2

    # 按模型ID过滤
    model_groups = await repo.list_all(model_id="gpt-4")
    assert len(model_groups) == 2

    # 同时按用户ID和模型ID过滤
    filtered_groups = await repo.list_all(user_id="user_001", model_id="gpt-4")
    assert len(filtered_groups) == 1
    assert filtered_groups[0].task_group_id == "tg_001"


@pytest.mark.asyncio
async def test_task_group_repo_delete(async_session):
    """测试删除任务组"""
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    repo = TaskGroupRepository(async_session)
    await repo.create("tg_001", "user_001", "gpt-4")

    # 删除存在的任务组
    result = await repo.delete("tg_001")
    assert result is True

    # 验证已删除
    task_group = await repo.get_by_id("tg_001")
    assert task_group is None

    # 删除不存在的任务组
    result = await repo.delete("non-existent")
    assert result is False


# ==================== TaskRepository 测试 ====================

@pytest.mark.asyncio
async def test_task_repo_create(async_session):
    """测试创建检测任务"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    # 创建任务
    repo = TaskRepository(async_session)
    start_time = datetime.now()
    task = await repo.create("task_001", "tg_001", "dataset_001", "running", start_time)

    assert task.task_id == "task_001"
    assert task.task_status == "running"
    assert task.end_time is None


@pytest.mark.asyncio
async def test_task_repo_get_by_id(async_session):
    """测试按ID查询任务"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", "tg_001", "dataset_001", "running", datetime.now())

    task = await repo.get_by_id("task_001")
    assert task is not None
    assert task.task_id == "task_001"


@pytest.mark.asyncio
async def test_task_repo_list_by_group(async_session):
    """测试按任务组ID查询任务列表"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")
    await group_repo.create("tg_002", "user_001", "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", "tg_001", "dataset_001", "running", datetime.now())
    await repo.create("task_002", "tg_001", "dataset_002", "completed", datetime.now())
    await repo.create("task_003", "tg_002", "dataset_001", "running", datetime.now())

    # 查询 tg_001 的任务
    tasks = await repo.list_by_group("tg_001")
    assert len(tasks) == 2

    # 查询 tg_002 的任务
    tasks = await repo.list_by_group("tg_002")
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_task_repo_update_status(async_session):
    """测试更新任务状态"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    repo = TaskRepository(async_session)
    start_time = datetime.now()
    await repo.create("task_001", "tg_001", "dataset_001", "running", start_time)

    # 更新状态
    end_time = datetime.now()
    result = await repo.update_status("task_001", "completed", end_time)
    assert result is True

    # 验证更新
    task = await repo.get_by_id("task_001")
    assert task.task_status == "completed"
    assert task.end_time == end_time

    # 更新不存在的任务
    result = await repo.update_status("non-existent", "completed")
    assert result is False


@pytest.mark.asyncio
async def test_task_repo_delete(async_session):
    """测试删除任务"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", "tg_001", "dataset_001", "running", datetime.now())

    # 删除任务
    result = await repo.delete("task_001")
    assert result is True

    # 验证已删除
    task = await repo.get_by_id("task_001")
    assert task is None


# ==================== ReportRepository 测试 ====================

@pytest.mark.asyncio
async def test_report_repo_create(async_session):
    """测试创建检测报告"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())

    # 创建报告
    repo = ReportRepository(async_session)
    report = await repo.create("report_001", "task_001")

    assert report.report_id == "report_001"
    assert report.task_id == "task_001"


@pytest.mark.asyncio
async def test_report_repo_get_by_task_id(async_session):
    """测试按任务ID查询报告"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())

    repo = ReportRepository(async_session)
    await repo.create("report_001", "task_001")

    report = await repo.get_by_task_id("task_001")
    assert report is not None
    assert report.report_id == "report_001"


@pytest.mark.asyncio
async def test_report_repo_list_all(async_session):
    """测试查询报告列表"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")
    await group_repo.create("tg_002", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())
    await task_repo.create("task_002", "tg_001", "dataset_002", "completed", datetime.now())
    await task_repo.create("task_003", "tg_002", "dataset_001", "completed", datetime.now())

    repo = ReportRepository(async_session)
    await repo.create("report_001", "task_001")
    await repo.create("report_002", "task_002")
    await repo.create("report_003", "task_003")

    # 查询所有报告
    all_reports = await repo.list_all()
    assert len(all_reports) == 3

    # 按任务组ID过滤
    group_reports = await repo.list_all(task_group_id="tg_001")
    assert len(group_reports) == 2


# ==================== ResultDataRepository 测试 ====================

@pytest.mark.asyncio
async def test_result_data_repo_create(async_session):
    """测试创建结果数据"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

    # 创建结果数据
    repo = ResultDataRepository(async_session)
    result_data = await repo.create(
        "result_001",
        "report_001",
        "prompt_injection",
        "Test output",
        "non_compliant"
    )

    assert result_data.result_data_id == "result_001"
    assert result_data.risk_subclass == "prompt_injection"


@pytest.mark.asyncio
async def test_result_data_repo_list_by_report(async_session):
    """测试按报告ID查询结果数据列表"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

    repo = ResultDataRepository(async_session)
    await repo.create("result_001", "report_001", "prompt_injection", "Output 1", "non_compliant")
    await repo.create("result_002", "report_001", "jailbreak", "Output 2", "compliant")

    # 查询报告的结果数据
    result_data_list = await repo.list_by_report("report_001")
    assert len(result_data_list) == 2


@pytest.mark.asyncio
async def test_result_data_repo_delete(async_session):
    """测试删除结果数据"""
    # 创建依赖数据
    model_repo = TargetModelRepository(async_session)
    await model_repo.create("gpt-4")

    group_repo = TaskGroupRepository(async_session)
    await group_repo.create("tg_001", "user_001", "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", "tg_001", "dataset_001", "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

    repo = ResultDataRepository(async_session)
    await repo.create("result_001", "report_001", "prompt_injection", "Output", "non_compliant")

    # 删除结果数据
    result = await repo.delete("result_001")
    assert result is True

    # 验证已删除
    result_data = await repo.get_by_id("result_001")
    assert result_data is None
