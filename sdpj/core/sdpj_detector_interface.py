"""SDPJDetector 接口定义"""
from typing import Protocol


class SDPJDetectorInterface(Protocol):
    """SDPJ检测内核接口"""

    async def init(self) -> None:
        """初始化检测器"""
        ...

    async def static_detect(self, model_id: str, dataset_id: int) -> dict:
        """执行静态检测算法

        Args:
            model_id: 目标模型ID
            dataset_id: 数据集ID

        Returns:
            检测结果字典
        """
        ...

    async def dynamic_detect(self, model_id: str, dataset_id: int) -> dict:
        """执行动态检测算法

        Args:
            model_id: 目标模型ID
            dataset_id: 数据集ID

        Returns:
            检测结果字典
        """
        ...
