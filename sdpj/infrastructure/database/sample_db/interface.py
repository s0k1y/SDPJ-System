"""SampleDB 接口定义

SampleDB 模块对外暴露的接口契约，定义检测样本数据库的所有能力。
DataProcessor 是唯一调用方。
"""

from typing import Optional, Protocol


class SampleDBInterface(Protocol):
    """检测样本数据库接口

    职责范围：
    - 数据集级能力：创建、删除、查询数据集
    - 样本级能力：添加、删除、查询检测样本

    不负责的边界：
    - 不解析数据集文件内容、不做格式校验（由 DataProcessor 与 UtilsLib 完成）
    - 不做调用方权限判定（由 DACManager 在调用前完成）
    - 不做分页/排序业务逻辑（由调用方按需处理）
    - 不做多模态/多编码处理（由 UtilsLib 完成）
    - 不解析 PoC 语义
    - 不维护样本版本
    - 不提供样本统计
    """

    # ==================== 数据集级能力 ====================

    async def create_dataset(self, name: str, risk_type: str) -> int:
        """创建检测数据集

        Args:
            name: 数据集名称
            risk_type: 安全风险类型（如「越狱攻击」「提示词注入」「安全基准」）

        Returns:
            新创建数据集的数据集 ID

        Raises:
            ValueError: 数据集名称在系统内重复时拒绝写入
        """
        ...

    async def delete_dataset(self, dataset_id: int) -> bool:
        """删除检测数据集

        后置条件：
        - 级联删除该数据集下的所有样本（满足外键完整性）

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...

    async def get_all_datasets(self) -> list[dict]:
        """查询数据集列表

        Returns:
            全部数据集元信息列表，每条包含：
            - dataset_id: 数据集 ID
            - name: 数据集名称
            - risk_type: 安全风险类型
            - created_at: 创建时间
        """
        ...

    async def get_dataset_by_id(self, dataset_id: int) -> Optional[dict]:
        """按 ID 查询单个数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            数据集元信息字典，包含：
            - dataset_id: 数据集 ID
            - name: 数据集名称
            - risk_type: 安全风险类型
            - created_at: 创建时间
            不存在时返回 None
        """
        ...

    async def get_datasets_by_risk_type(self, risk_type: str) -> list[dict]:
        """按安全风险类型筛选数据集

        Args:
            risk_type: 安全风险类型（如「越狱攻击」「提示词注入」「安全基准」）

        Returns:
            匹配的数据集列表，每条包含：
            - dataset_id: 数据集 ID
            - name: 数据集名称
            - risk_type: 安全风险类型
            - created_at: 创建时间
        """
        ...

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
        ...

    async def delete_sample(self, sample_id: int) -> bool:
        """删除检测样本

        Args:
            sample_id: 样本 ID

        Returns:
            删除结果（True 表示成功）
        """
        ...

    async def get_samples_by_dataset(self, dataset_id: int) -> list[dict]:
        """按数据集 ID 查询所有样本

        Args:
            dataset_id: 数据集 ID

        Returns:
            该数据集下全部样本列表，每条包含：
            - sample_id: 样本 ID
            - subtype: 风险具体子类 ST
            - poc: 漏洞概念验证数据 PoC
            - dataset_id: 所属数据集 ID
            - created_at: 创建时间
        """
        ...

    async def get_samples_by_risk_type(self, risk_type: str) -> list[dict]:
        """按安全风险类型查询所有样本（单次 JOIN 查询）

        Args:
            risk_type: 安全风险类型

        Returns:
            匹配的所有样本列表，每条包含：
            - sample_id: 样本 ID
            - subtype: 风险具体子类 ST
            - poc: 漏洞概念验证数据 PoC
            - dataset_id: 所属数据集 ID
            - created_at: 创建时间
        """
        ...

    async def get_sample_by_id(self, sample_id: int) -> Optional[dict]:
        """按 ID 查询单条样本

        Args:
            sample_id: 样本 ID

        Returns:
            单条样本详情字典，包含：
            - sample_id: 样本 ID
            - subtype: 风险具体子类 ST
            - poc: 漏洞概念验证数据 PoC
            - dataset_id: 所属数据集 ID
            - created_at: 创建时间
            不存在时返回 None
        """
        ...
