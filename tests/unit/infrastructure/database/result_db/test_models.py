"""ResultDB 模型单元测试

测试 ORM 模型的基本功能和关系.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sdpj.infrastructure.database.result_db.models import (
    Base,
    TaskGroup,
    DetectionTask,
    DetectionReport,
    ResultData,
)
from typing import Any


@pytest.fixture
async def async_session() -> None:
    """创建测试用的异步数据库会话"""
    from sdpj.infrastructure.database.user_db.models import User  # noqa
    from sdpj.infrastructure.database.sample_db.models import Dataset  # noqa

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        session.add_all(
            [
                User(username="u1", password="pw"),
                Dataset(name="ds1", risk_type="jailbreak"),
            ]
        )
        await session.commit()

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_task_group_creation(async_session: Any) -> None:
    """测试任务组创建"""
    task_group = TaskGroup(task_group_id="tg_001", user_id=1, model_id="gpt-4")
    async_session.add(task_group)
    await async_session.commit()

    assert task_group.task_group_id == "tg_001"
    assert task_group.user_id == 1
    assert task_group.model_id == "gpt-4"


@pytest.mark.asyncio
async def test_detection_task_creation(async_session: Any) -> None:
    """测试检测任务创建"""
    task_group = TaskGroup(task_group_id="tg_001", user_id=1, model_id="gpt-4")
    async_session.add(task_group)
    await async_session.flush()

    start_time = datetime.now()
    task = DetectionTask(
        task_id="task_001",
        task_group_id="tg_001",
        dataset_id=1,
        task_status="running",
        start_time=start_time,
    )
    async_session.add(task)
    await async_session.commit()

    assert task.task_id == "task_001"
    assert task.task_status == "running"
    assert task.end_time is None


@pytest.mark.asyncio
async def test_detection_report_creation(async_session: Any) -> None:
    """测试检测报告创建"""
    task_group = TaskGroup(task_group_id="tg_001", user_id=1, model_id="gpt-4")
    async_session.add(task_group)
    await async_session.flush()

    task = DetectionTask(
        task_id="task_001",
        task_group_id="tg_001",
        dataset_id=1,
        task_status="completed",
        start_time=datetime.now(),
    )
    async_session.add(task)
    await async_session.flush()

    report = DetectionReport(report_id="report_001", task_id="task_001")
    async_session.add(report)
    await async_session.commit()

    assert report.report_id == "report_001"
    assert report.task_id == "task_001"


@pytest.mark.asyncio
async def test_result_data_creation(async_session: Any) -> None:
    """测试结果数据创建"""
    task_group = TaskGroup(task_group_id="tg_001", user_id=1, model_id="gpt-4")
    async_session.add(task_group)
    await async_session.flush()

    task = DetectionTask(
        task_id="task_001",
        task_group_id="tg_001",
        dataset_id=1,
        task_status="completed",
        start_time=datetime.now(),
    )
    async_session.add(task)
    await async_session.flush()

    report = DetectionReport(report_id="report_001", task_id="task_001")
    async_session.add(report)
    await async_session.flush()

    result_data = ResultData(
        result_data_id="result_001",
        report_id="report_001",
        risk_subclass="prompt_injection",
        model_output="I will help you with that.",
        compliance_result="non_compliant",
    )
    async_session.add(result_data)
    await async_session.commit()

    assert result_data.result_data_id == "result_001"
    assert result_data.risk_subclass == "prompt_injection"
    assert result_data.compliance_result == "non_compliant"


@pytest.mark.asyncio
async def test_cascade_delete_task_group(async_session: Any) -> None:
    """测试任务组级联删除"""
    task_group = TaskGroup(task_group_id="tg_001", user_id=1, model_id="gpt-4")
    async_session.add(task_group)
    await async_session.flush()

    task = DetectionTask(
        task_id="task_001",
        task_group_id="tg_001",
        dataset_id=1,
        task_status="completed",
        start_time=datetime.now(),
    )
    async_session.add(task)
    await async_session.flush()

    report = DetectionReport(report_id="report_001", task_id="task_001")
    async_session.add(report)
    await async_session.flush()

    result_data = ResultData(
        result_data_id="result_001",
        report_id="report_001",
        risk_subclass="prompt_injection",
        model_output="Test output",
        compliance_result="non_compliant",
    )
    async_session.add(result_data)
    await async_session.commit()

    await async_session.delete(task_group)
    await async_session.commit()

    from sqlalchemy import select

    task_result = await async_session.execute(
        select(DetectionTask).where(DetectionTask.task_id == "task_001")
    )
    assert task_result.scalar_one_or_none() is None

    report_result = await async_session.execute(
        select(DetectionReport).where(DetectionReport.report_id == "report_001")
    )
    assert report_result.scalar_one_or_none() is None

    result_result = await async_session.execute(
        select(ResultData).where(ResultData.result_data_id == "result_001")
    )
    assert result_result.scalar_one_or_none() is None
