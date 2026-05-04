"""ResultDB 仓储层单元测试

测试所有仓储类的数据访问操作。
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sdpj.infrastructure.database.result_db.models import Base, TaskGroup, DetectionTask
from sdpj.infrastructure.database.result_db.repositories import (
    TaskGroupRepository,
    TaskRepository,
    ReportRepository,
    ResultDataRepository,
)


@pytest.fixture
async def async_session():
    """创建测试用的异步数据库会话"""
    from sdpj.infrastructure.database.user_db.models import User  # noqa
    from sdpj.infrastructure.database.sample_db.models import Dataset  # noqa
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        session.add_all([
            User(username="user_001", password="pw"),
            User(username="user_002", password="pw"),
        ])
        await session.flush()
        session.add_all([
            Dataset(name="dataset_001", risk_type="jailbreak"),
            Dataset(name="dataset_002", risk_type="injection"),
        ])
        await session.commit()

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# ==================== TaskGroupRepository 测试 ====================

@pytest.mark.asyncio
async def test_task_group_repo_create(async_session):
    """测试创建任务组"""
    repo = TaskGroupRepository(async_session)
    task_group = await repo.create(1, "gpt-4")

    assert task_group.task_group_id.startswith("tg_")
    assert task_group.user_id == 1
    assert task_group.model_id == "gpt-4"


@pytest.mark.asyncio
async def test_task_group_repo_get_by_id(async_session):
    """测试按ID查询任务组"""
    repo = TaskGroupRepository(async_session)
    created = await repo.create(1, "gpt-4")

    task_group = await repo.get_by_id(created.task_group_id)
    assert task_group is not None
    assert task_group.task_group_id == created.task_group_id


@pytest.mark.asyncio
async def test_task_group_repo_list_all(async_session):
    """测试查询任务组列表"""
    repo = TaskGroupRepository(async_session)
    tg1 = await repo.create(1, "gpt-4")
    tg2 = await repo.create(1, "claude-3")
    tg3 = await repo.create(2, "gpt-4")

    all_groups = await repo.list_all()
    assert len(all_groups) == 3

    user_groups = await repo.list_all(user_id=1)
    assert len(user_groups) == 2

    model_groups = await repo.list_all(model_id="gpt-4")
    assert len(model_groups) == 2

    filtered_groups = await repo.list_all(user_id=1, model_id="gpt-4")
    assert len(filtered_groups) == 1
    assert filtered_groups[0].task_group_id == tg1.task_group_id


@pytest.mark.asyncio
async def test_task_group_repo_delete(async_session):
    """测试删除任务组"""
    repo = TaskGroupRepository(async_session)
    created = await repo.create(1, "gpt-4")
    tg_id = created.task_group_id

    result = await repo.delete(tg_id)
    assert result is True

    task_group = await repo.get_by_id(tg_id)
    assert task_group is None

    result = await repo.delete("non-existent")
    assert result is False


# ==================== TaskRepository 测试 ====================

@pytest.mark.asyncio
async def test_task_repo_create(async_session):
    """测试创建检测任务"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    repo = TaskRepository(async_session)
    start_time = datetime.now()
    task = await repo.create("task_001", tg.task_group_id, 1, "running", start_time)

    assert task.task_id == "task_001"
    assert task.task_status == "running"
    assert task.end_time is None

@pytest.mark.asyncio
async def test_task_repo_get_by_id(async_session):
    """测试按ID查询任务"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", tg.task_group_id, 1, "running", datetime.now())

    task = await repo.get_by_id("task_001")
    assert task is not None
    assert task.task_id == "task_001"


@pytest.mark.asyncio
async def test_task_repo_list_by_group(async_session):
    """测试按任务组ID查询任务列表"""
    group_repo = TaskGroupRepository(async_session)
    tg1 = await group_repo.create(1, "gpt-4")
    tg2 = await group_repo.create(1, "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", tg1.task_group_id, 1, "running", datetime.now())
    await repo.create("task_002", tg1.task_group_id, 2, "completed", datetime.now())
    await repo.create("task_003", tg2.task_group_id, 1, "running", datetime.now())

    tasks = await repo.list_by_group(tg1.task_group_id)
    assert len(tasks) == 2

    tasks = await repo.list_by_group(tg2.task_group_id)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_task_repo_update_status(async_session):
    """测试更新任务状态"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", tg.task_group_id, 1, "running", datetime.now())

    end_time = datetime.now()
    result = await repo.update_status("task_001", "completed", end_time)
    assert result is True

    task = await repo.get_by_id("task_001")
    assert task.task_status == "completed"
    assert task.end_time == end_time

    result = await repo.update_status("non-existent", "completed")
    assert result is False


@pytest.mark.asyncio
async def test_task_repo_delete(async_session):
    """测试删除任务"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    repo = TaskRepository(async_session)
    await repo.create("task_001", tg.task_group_id, 1, "running", datetime.now())

    result = await repo.delete("task_001")
    assert result is True

    task = await repo.get_by_id("task_001")
    assert task is None

# ==================== ReportRepository 测试 ====================

@pytest.mark.asyncio
async def test_report_repo_create(async_session):
    """测试创建检测报告"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg.task_group_id, 1, "completed", datetime.now())

    repo = ReportRepository(async_session)
    report = await repo.create("report_001", "task_001")

    assert report.report_id == "report_001"
    assert report.task_id == "task_001"


@pytest.mark.asyncio
async def test_report_repo_get_by_task_id(async_session):
    """测试按任务ID查询报告"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg.task_group_id, 1, "completed", datetime.now())

    repo = ReportRepository(async_session)
    await repo.create("report_001", "task_001")

    report = await repo.get_by_task_id("task_001")
    assert report is not None
    assert report.report_id == "report_001"


@pytest.mark.asyncio
async def test_report_repo_list_all(async_session):
    """测试查询报告列表"""
    group_repo = TaskGroupRepository(async_session)
    tg1 = await group_repo.create(1, "gpt-4")
    tg2 = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg1.task_group_id, 1, "completed", datetime.now())
    await task_repo.create("task_002", tg1.task_group_id, 2, "completed", datetime.now())
    await task_repo.create("task_003", tg2.task_group_id, 1, "completed", datetime.now())

    repo = ReportRepository(async_session)
    await repo.create("report_001", "task_001")
    await repo.create("report_002", "task_002")
    await repo.create("report_003", "task_003")

    all_reports = await repo.list_all()
    assert len(all_reports) == 3

    group_reports = await repo.list_all(task_group_id=tg1.task_group_id)
    assert len(group_reports) == 2


# ==================== ResultDataRepository 测试 ====================

@pytest.mark.asyncio
async def test_result_data_repo_create(async_session):
    """测试创建结果数据"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg.task_group_id, 1, "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

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
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg.task_group_id, 1, "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

    repo = ResultDataRepository(async_session)
    await repo.create("result_001", "report_001", "prompt_injection", "Output 1", "non_compliant")
    await repo.create("result_002", "report_001", "jailbreak", "Output 2", "compliant")

    result_data_list = await repo.list_by_report("report_001")
    assert len(result_data_list) == 2


@pytest.mark.asyncio
async def test_result_data_repo_delete(async_session):
    """测试删除结果数据"""
    group_repo = TaskGroupRepository(async_session)
    tg = await group_repo.create(1, "gpt-4")

    task_repo = TaskRepository(async_session)
    await task_repo.create("task_001", tg.task_group_id, 1, "completed", datetime.now())

    report_repo = ReportRepository(async_session)
    await report_repo.create("report_001", "task_001")

    repo = ResultDataRepository(async_session)
    await repo.create("result_001", "report_001", "prompt_injection", "Output", "non_compliant")

    result = await repo.delete("result_001")
    assert result is True

    result_data = await repo.get_by_id("result_001")
    assert result_data is None
