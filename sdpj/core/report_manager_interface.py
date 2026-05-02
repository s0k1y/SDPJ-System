"""ReportManager 接口定义"""
from typing import Protocol


class ReportManagerInterface(Protocol):
    """检测报告管理接口"""

    async def init(self) -> None:
        """初始化报告管理器"""
        ...

    async def generate_report(self, task_id: str, results: list) -> int:
        """生成检测报告

        Args:
            task_id: 任务ID
            results: 检测结果列表

        Returns:
            报告ID
        """
        ...

    async def get_report(self, report_id: int) -> dict:
        """获取报告

        Args:
            report_id: 报告ID

        Returns:
            报告数据
        """
        ...

    async def list_reports(self, user_id: int) -> list:
        """列出用户的所有报告

        Args:
            user_id: 用户ID

        Returns:
            报告列表
        """
        ...

    def calculate_statistics(self, results: list) -> dict:
        """计算统计数据

        Args:
            results: 检测结果列表

        Returns:
            统计数据字典
        """
        ...
