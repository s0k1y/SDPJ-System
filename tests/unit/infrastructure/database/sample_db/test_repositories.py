"""SampleDB 仓储层单元测试"""

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sdpj.infrastructure.database.sample_db.models import Base, Dataset, DetectionSample
from sdpj.infrastructure.database.sample_db.repositories import DatasetRepository, SampleRepository


@pytest_asyncio.fixture
async def async_session():
    """创建测试用的异步数据库会话"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_fk(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


# ==================== DatasetRepository 测试 ====================


@pytest.mark.asyncio
async def test_dataset_repo_create(async_session):
    """测试数据集仓储创建功能"""
    repo = DatasetRepository(async_session)
    dataset = await repo.create("测试数据集", "越狱攻击")
    await async_session.commit()

    assert dataset.dataset_id is not None
    assert dataset.name == "测试数据集"
    assert dataset.risk_type == "越狱攻击"


@pytest.mark.asyncio
async def test_dataset_repo_create_duplicate_name(async_session):
    """测试数据集仓储创建重复名称时抛出异常"""
    repo = DatasetRepository(async_session)
    await repo.create("重复名称", "提示词注入")
    await async_session.commit()

    with pytest.raises(ValueError, match="数据集名称 '重复名称' 已存在"):
        await repo.create("重复名称", "越狱攻击")


@pytest.mark.asyncio
async def test_dataset_repo_get_by_id(async_session):
    """测试数据集仓储按 ID 查询"""
    repo = DatasetRepository(async_session)
    dataset = await repo.create("查询测试", "安全基准")
    await async_session.commit()

    found = await repo.get_by_id(dataset.dataset_id)
    assert found is not None
    assert found.dataset_id == dataset.dataset_id
    assert found.name == "查询测试"

    not_found = await repo.get_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_dataset_repo_get_by_name(async_session):
    """测试数据集仓储按名称查询"""
    repo = DatasetRepository(async_session)
    await repo.create("名称查询测试", "越狱攻击")
    await async_session.commit()

    found = await repo.get_by_name("名称查询测试")
    assert found is not None
    assert found.name == "名称查询测试"

    not_found = await repo.get_by_name("不存在的名称")
    assert not_found is None


@pytest.mark.asyncio
async def test_dataset_repo_get_all(async_session):
    """测试数据集仓储查询所有数据集"""
    repo = DatasetRepository(async_session)
    await repo.create("数据集1", "越狱攻击")
    await repo.create("数据集2", "提示词注入")
    await repo.create("数据集3", "安全基准")
    await async_session.commit()

    all_datasets = await repo.get_all()
    assert len(all_datasets) == 3


@pytest.mark.asyncio
async def test_dataset_repo_get_by_risk_type(async_session):
    """测试数据集仓储按风险类型筛选"""
    repo = DatasetRepository(async_session)
    await repo.create("越狱数据集1", "越狱攻击")
    await repo.create("越狱数据集2", "越狱攻击")
    await repo.create("注入数据集", "提示词注入")
    await async_session.commit()

    jailbreak_datasets = await repo.get_by_risk_type("越狱攻击")
    assert len(jailbreak_datasets) == 2

    injection_datasets = await repo.get_by_risk_type("提示词注入")
    assert len(injection_datasets) == 1


@pytest.mark.asyncio
async def test_dataset_repo_delete(async_session):
    """测试数据集仓储删除功能"""
    repo = DatasetRepository(async_session)
    dataset = await repo.create("待删除数据集", "越狱攻击")
    await async_session.commit()

    result = await repo.delete(dataset.dataset_id)
    await async_session.commit()
    assert result is True

    deleted = await repo.get_by_id(dataset.dataset_id)
    assert deleted is None

    # 删除不存在的数据集
    result = await repo.delete(99999)
    assert result is False


# ==================== SampleRepository 测试 ====================


@pytest.mark.asyncio
async def test_sample_repo_create(async_session):
    """测试样本仓储创建功能"""
    # 先创建数据集
    dataset_repo = DatasetRepository(async_session)
    dataset = await dataset_repo.create("样本测试数据集", "越狱攻击")
    await async_session.commit()

    # 创建样本
    sample_repo = SampleRepository(async_session)
    sample = await sample_repo.create("普通越狱", "Test PoC", dataset.dataset_id)
    await async_session.commit()

    assert sample.sample_id is not None
    assert sample.subtype == "普通越狱"
    assert sample.poc == "Test PoC"
    assert sample.dataset_id == dataset.dataset_id


@pytest.mark.asyncio
async def test_sample_repo_create_invalid_dataset(async_session):
    """测试样本仓储创建时数据集不存在抛出异常"""
    sample_repo = SampleRepository(async_session)

    with pytest.raises(ValueError, match="所属数据集 ID 99999 不存在"):
        await sample_repo.create("子类", "PoC", 99999)


@pytest.mark.asyncio
async def test_sample_repo_get_by_id(async_session):
    """测试样本仓储按 ID 查询"""
    # 创建数据集和样本
    dataset_repo = DatasetRepository(async_session)
    dataset = await dataset_repo.create("查询测试数据集", "提示词注入")
    await async_session.commit()

    sample_repo = SampleRepository(async_session)
    sample = await sample_repo.create("注入子类", "PoC内容", dataset.dataset_id)
    await async_session.commit()

    # 查询样本
    found = await sample_repo.get_by_id(sample.sample_id)
    assert found is not None
    assert found.sample_id == sample.sample_id
    assert found.subtype == "注入子类"

    not_found = await sample_repo.get_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_sample_repo_get_by_dataset(async_session):
    """测试样本仓储按数据集查询"""
    # 创建数据集
    dataset_repo = DatasetRepository(async_session)
    dataset = await dataset_repo.create("多样本数据集", "安全基准")
    await async_session.commit()

    # 创建多个样本
    sample_repo = SampleRepository(async_session)
    await sample_repo.create("子类1", "PoC1", dataset.dataset_id)
    await sample_repo.create("子类2", "PoC2", dataset.dataset_id)
    await sample_repo.create("子类3", "PoC3", dataset.dataset_id)
    await async_session.commit()

    # 查询数据集下的所有样本
    samples = await sample_repo.get_by_dataset(dataset.dataset_id)
    assert len(samples) == 3


@pytest.mark.asyncio
async def test_sample_repo_delete(async_session):
    """测试样本仓储删除功能"""
    # 创建数据集和样本
    dataset_repo = DatasetRepository(async_session)
    dataset = await dataset_repo.create("删除测试数据集", "越狱攻击")
    await async_session.commit()

    sample_repo = SampleRepository(async_session)
    sample = await sample_repo.create("待删除样本", "PoC", dataset.dataset_id)
    await async_session.commit()

    # 删除样本
    result = await sample_repo.delete(sample.sample_id)
    await async_session.commit()
    assert result is True

    deleted = await sample_repo.get_by_id(sample.sample_id)
    assert deleted is None

    # 删除不存在的样本
    result = await sample_repo.delete(99999)
    assert result is False
