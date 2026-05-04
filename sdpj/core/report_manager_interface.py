"""ReportManager 接口定义

被依赖模块: StateScheduler
"""
from typing import Protocol, Optional, Literal


class ReportManagerInterface(Protocol):
    """检测报告管理接口"""

    async def generate_static_report(self, task_group_id: str) -> dict:
        """生成静态检测报告"""
        ...

    async def generate_dynamic_report(self, task_group_id: str) -> dict:
        """生成动态检测报告"""
        ...

    def calculate_statistics(self, results: list[dict]) -> dict:
        """计算报告统计指标"""
        ...

    async def list_reports(
        self, user_id: Optional[str] = None, model_id: Optional[str] = None
    ) -> list[dict]:
        """查询检测报告列表"""
        ...

    async def view_report(self, task_group_id: str) -> dict:
        """查看单份检测报告"""
        ...

    async def delete_report(
        self,
        task_group_id: Optional[str] = None,
        task_id: Optional[str] = None,
        report_id: Optional[str] = None,
        result_data_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """删除检测报告"""
        ...

    async def export_report(
        self, task_group_id: str, target_format: Literal["json", "yaml"] = "json"
    ) -> str:
        """导出检测报告文件"""
        ...

    async def prepare_visualization_data(self, task_group_id: str) -> dict:
        """准备可视化图表数据"""
        ...

    async def get_compliance_statistics(self) -> dict:
        """获取全局合规统计"""
        ...
