"""SampleDB 实现

实现 SampleDBInterface 接口，提供检测样本数据库的完整功能。
"""

from typing import Optional
from .interface import SampleDBInterface
from .session import SampleDBSessionManager
from .repositories import DatasetRepository, SampleRepository


class SampleDB:
    """检测样本数据库实现

    实现 SampleDBInterface 定义的所有能力。
    DataProcessor 是唯一调用方。
    """

    def __init__(self, session_manager: SampleDBSessionManager):
        """初始化 SampleDB

        Args:
            session_manager: 数据库会话管理器
        """
        self.session_manager = session_manager

    # ==================== 数据集级能力 ====================

    async def create_dataset(self, name: str, risk_type: str) -> int:
        """创建检测数据集

        Args:
            name: 数据集名称
            risk_type: 安全风险类型

        Returns:
            新创建数据集的数据集 ID

        Raises:
            ValueError: 数据集名称在系统内重复时拒绝写入
        """
        async with self.session_manager.get_session() as session:
            repo = DatasetRepository(session)
            dataset = await repo.create(name, risk_type)
            await session.commit()
            return dataset.dataset_id

    async def delete_dataset(self, dataset_id: int) -> bool:
        """删除检测数据集

        后置条件：
        - 级联删除该数据集下的所有样本（满足外键完整性）

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果（True 表示成功）
        """
        async with self.session_manager.get_session() as session:
            repo = DatasetRepository(session)
            result = await repo.delete(dataset_id)
            await session.commit()
            return result

    async def get_all_datasets(self) -> list[dict]:
        """查询数据集列表

        Returns:
            全部数据集元信息列表
        """
        async with self.session_manager.get_session() as session:
            repo = DatasetRepository(session)
            datasets = await repo.get_all()
            return [
                {
                    "dataset_id": ds.dataset_id,
                    "name": ds.name,
                    "risk_type": ds.risk_type,
                    "created_at": ds.created_at,
                }
                for ds in datasets
            ]

    async def get_dataset_by_id(self, dataset_id: int) -> Optional[dict]:
        """按 ID 查询单个数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            数据集元信息字典，不存在时返回 None
        """
        async with self.session_manager.get_session() as session:
            repo = DatasetRepository(session)
            dataset = await repo.get_by_id(dataset_id)
            if dataset is None:
                return None
            return {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "risk_type": dataset.risk_type,
                "created_at": dataset.created_at,
            }

    async def get_datasets_by_risk_type(self, risk_type: str) -> list[dict]:
        """按安全风险类型筛选数据集

        Args:
            risk_type: 安全风险类型

        Returns:
            匹配的数据集列表
        """
        async with self.session_manager.get_session() as session:
            repo = DatasetRepository(session)
            datasets = await repo.get_by_risk_type(risk_type)
            return [
                {
                    "dataset_id": ds.dataset_id,
                    "name": ds.name,
                    "risk_type": ds.risk_type,
                    "created_at": ds.created_at,
                }
                for ds in datasets
            ]

    # ==================== 样本级能力 ====================

    async def add_sample(self, subtype: str, poc: str, dataset_id: int) -> int:
        """添加检测样本到指定数据集

        Args:
            subtype: 风险具体子类 ST
            poc: 漏洞概念验证数据 PoC
            dataset_id: 所属数据集 ID

        Returns:
            新创建样本的样本 ID

        Raises:
            ValueError: 所属数据集 ID 不存在时拒绝写入
        """
        async with self.session_manager.get_session() as session:
            repo = SampleRepository(session)
            sample = await repo.create(subtype, poc, dataset_id)
            await session.commit()
            return sample.sample_id

    async def delete_sample(self, sample_id: int) -> bool:
        """删除检测样本

        Args:
            sample_id: 样本 ID

        Returns:
            删除结果（True 表示成功）
        """
        async with self.session_manager.get_session() as session:
            repo = SampleRepository(session)
            result = await repo.delete(sample_id)
            await session.commit()
            return result

    async def get_samples_by_dataset(self, dataset_id: int) -> list[dict]:
        """按数据集 ID 查询所有样本

        Args:
            dataset_id: 数据集 ID

        Returns:
            该数据集下全部样本列表
        """
        async with self.session_manager.get_session() as session:
            repo = SampleRepository(session)
            samples = await repo.get_by_dataset(dataset_id)
            return [
                {
                    "sample_id": s.sample_id,
                    "subtype": s.subtype,
                    "poc": s.poc,
                    "dataset_id": s.dataset_id,
                    "created_at": s.created_at,
                }
                for s in samples
            ]

    async def get_sample_by_id(self, sample_id: int) -> Optional[dict]:
        """按 ID 查询单条样本

        Args:
            sample_id: 样本 ID

        Returns:
            单条样本详情字典，不存在时返回 None
        """
        async with self.session_manager.get_session() as session:
            repo = SampleRepository(session)
            sample = await repo.get_by_id(sample_id)
            if sample is None:
                return None
            return {
                "sample_id": sample.sample_id,
                "subtype": sample.subtype,
                "poc": sample.poc,
                "dataset_id": sample.dataset_id,
                "created_at": sample.created_at,
            }
