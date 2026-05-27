"""SampleDB 实现单元测试

测试 SampleDB 类实现的所有接口方法.
"""

import pytest
import pytest_asyncio
from sdpj.infrastructure.database.sample_db import SampleDB, SampleDBSessionManager
from typing import Any


@pytest_asyncio.fixture
async def sample_db() -> None:
    """创建测试用的 SampleDB 实例"""
    session_manager = SampleDBSessionManager("sqlite+aiosqlite:///:memory:")
    await session_manager.initialize()
    await session_manager.create_tables()

    db = SampleDB(session_manager)
    yield db

    await session_manager.close()


# ==================== 数据集级能力测试 ====================


@pytest.mark.asyncio
async def test_create_dataset(sample_db: Any) -> None:
    """测试创建数据集"""
    dataset_id = await sample_db.create_dataset("测试数据集", "越狱攻击")
    assert dataset_id is not None
    assert isinstance(dataset_id, int)


@pytest.mark.asyncio
async def test_create_dataset_duplicate_name(sample_db: Any) -> None:
    """测试创建重复名称的数据集抛出异常"""
    await sample_db.create_dataset("重复名称", "提示词注入")

    with pytest.raises(ValueError, match="数据集名称 '重复名称' 已存在"):
        await sample_db.create_dataset("重复名称", "越狱攻击")


@pytest.mark.asyncio
async def test_get_dataset_by_id(sample_db: Any) -> None:
    """测试按 ID 查询数据集"""
    dataset_id = await sample_db.create_dataset("查询测试", "安全基准")

    dataset = await sample_db.get_dataset_by_id(dataset_id)
    assert dataset is not None
    assert dataset["dataset_id"] == dataset_id
    assert dataset["name"] == "查询测试"
    assert dataset["risk_type"] == "安全基准"
    assert "created_at" in dataset

    # 查询不存在的数据集
    not_found = await sample_db.get_dataset_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_all_datasets(sample_db: Any) -> None:
    """测试查询所有数据集"""
    await sample_db.create_dataset("数据集1", "越狱攻击")
    await sample_db.create_dataset("数据集2", "提示词注入")
    await sample_db.create_dataset("数据集3", "安全基准")

    datasets = await sample_db.get_all_datasets()
    assert len(datasets) == 3
    assert all("dataset_id" in ds for ds in datasets)
    assert all("name" in ds for ds in datasets)
    assert all("risk_type" in ds for ds in datasets)


@pytest.mark.asyncio
async def test_get_datasets_by_risk_type(sample_db: Any) -> None:
    """测试按风险类型筛选数据集"""
    await sample_db.create_dataset("越狱数据集1", "越狱攻击")
    await sample_db.create_dataset("越狱数据集2", "越狱攻击")
    await sample_db.create_dataset("注入数据集", "提示词注入")

    jailbreak_datasets = await sample_db.get_datasets_by_risk_type("越狱攻击")
    assert len(jailbreak_datasets) == 2

    injection_datasets = await sample_db.get_datasets_by_risk_type("提示词注入")
    assert len(injection_datasets) == 1

    empty_datasets = await sample_db.get_datasets_by_risk_type("不存在的类型")
    assert len(empty_datasets) == 0


@pytest.mark.asyncio
async def test_delete_dataset(sample_db: Any) -> None:
    """测试删除数据集"""
    dataset_id = await sample_db.create_dataset("待删除数据集", "越狱攻击")

    result = await sample_db.delete_dataset(dataset_id)
    assert result is True

    deleted = await sample_db.get_dataset_by_id(dataset_id)
    assert deleted is None

    # 删除不存在的数据集
    result = await sample_db.delete_dataset(99999)
    assert result is False


@pytest.mark.asyncio
async def test_delete_dataset_cascade(sample_db: Any) -> None:
    """测试删除数据集时级联删除样本"""
    # 创建数据集和样本
    dataset_id = await sample_db.create_dataset("级联删除测试", "越狱攻击")
    sample_id1 = await sample_db.add_sample("子类1", "PoC1", dataset_id)
    sample_id2 = await sample_db.add_sample("子类2", "PoC2", dataset_id)

    # 删除数据集
    await sample_db.delete_dataset(dataset_id)

    # 验证样本也被删除
    sample1 = await sample_db.get_sample_by_id(sample_id1)
    sample2 = await sample_db.get_sample_by_id(sample_id2)
    assert sample1 is None
    assert sample2 is None


# ==================== 样本级能力测试 ====================


@pytest.mark.asyncio
async def test_add_sample(sample_db: Any) -> None:
    """测试添加检测样本"""
    dataset_id = await sample_db.create_dataset("样本测试数据集", "提示词注入")

    sample_id = await sample_db.add_sample("普通注入", "Test PoC", dataset_id)
    assert sample_id is not None
    assert isinstance(sample_id, int)


@pytest.mark.asyncio
async def test_add_sample_invalid_dataset(sample_db: Any) -> None:
    """测试添加样本时数据集不存在抛出异常"""
    with pytest.raises(ValueError, match="所属数据集 ID 99999 不存在"):
        await sample_db.add_sample("子类", "PoC", 99999)


@pytest.mark.asyncio
async def test_get_sample_by_id(sample_db: Any) -> None:
    """测试按 ID 查询样本"""
    dataset_id = await sample_db.create_dataset("查询样本测试", "越狱攻击")
    sample_id = await sample_db.add_sample("越狱子类", "PoC内容", dataset_id)

    sample = await sample_db.get_sample_by_id(sample_id)
    assert sample is not None
    assert sample["sample_id"] == sample_id
    assert sample["subtype"] == "越狱子类"
    assert sample["poc"] == "PoC内容"
    assert sample["dataset_id"] == dataset_id
    assert "created_at" in sample

    # 查询不存在的样本
    not_found = await sample_db.get_sample_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_samples_by_dataset(sample_db: Any) -> None:
    """测试按数据集查询所有样本"""
    dataset_id = await sample_db.create_dataset("多样本数据集", "安全基准")

    await sample_db.add_sample("子类1", "PoC1", dataset_id)
    await sample_db.add_sample("子类2", "PoC2", dataset_id)
    await sample_db.add_sample("子类3", "PoC3", dataset_id)

    samples = await sample_db.get_samples_by_dataset(dataset_id)
    assert len(samples) == 3
    assert all("sample_id" in s for s in samples)
    assert all("subtype" in s for s in samples)
    assert all("poc" in s for s in samples)
    assert all(s["dataset_id"] == dataset_id for s in samples)


@pytest.mark.asyncio
async def test_delete_sample(sample_db: Any) -> None:
    """测试删除样本"""
    dataset_id = await sample_db.create_dataset("删除样本测试", "提示词注入")
    sample_id = await sample_db.add_sample("待删除样本", "PoC", dataset_id)

    result = await sample_db.delete_sample(sample_id)
    assert result is True

    deleted = await sample_db.get_sample_by_id(sample_id)
    assert deleted is None

    # 删除不存在的样本
    result = await sample_db.delete_sample(99999)
    assert result is False


@pytest.mark.asyncio
async def test_sample_long_poc(sample_db: Any) -> None:
    """测试长文本 PoC 存储"""
    dataset_id = await sample_db.create_dataset("长文本测试", "越狱攻击")

    long_poc = "A" * 10000  # 10000 字符的长文本
    sample_id = await sample_db.add_sample("长文本子类", long_poc, dataset_id)

    sample = await sample_db.get_sample_by_id(sample_id)
    assert sample is not None
    assert sample["poc"] == long_poc
    assert len(sample["poc"]) == 10000


# ==================== 综合场景测试 ====================


@pytest.mark.asyncio
async def test_complete_workflow(sample_db: Any) -> None:
    """测试完整工作流:创建数据集 -> 添加样本 -> 查询 -> 删除"""
    # 1. 创建数据集
    dataset_id = await sample_db.create_dataset("完整流程测试", "越狱攻击")
    assert dataset_id is not None

    # 2. 添加多个样本
    sample_ids = []
    for i in range(5):
        sample_id = await sample_db.add_sample(f"子类{i}", f"PoC{i}", dataset_id)
        sample_ids.append(sample_id)

    # 3. 查询数据集
    dataset = await sample_db.get_dataset_by_id(dataset_id)
    assert dataset["name"] == "完整流程测试"

    # 4. 查询样本列表
    samples = await sample_db.get_samples_by_dataset(dataset_id)
    assert len(samples) == 5

    # 5. 删除单个样本
    await sample_db.delete_sample(sample_ids[0])
    samples = await sample_db.get_samples_by_dataset(dataset_id)
    assert len(samples) == 4

    # 6. 删除数据集(级联删除剩余样本)
    await sample_db.delete_dataset(dataset_id)
    dataset = await sample_db.get_dataset_by_id(dataset_id)
    assert dataset is None
