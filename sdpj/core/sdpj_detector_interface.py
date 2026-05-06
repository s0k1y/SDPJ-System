"""SDPJDetector 接口定义

被依赖模块: StateScheduler
"""
from typing import Callable, Protocol, Optional


class SDPJDetectorInterface(Protocol):
    """SDPJ 检测内核接口"""

    async def run_static_detection(self, model_id: str, user_id: str, dataset_ids: list[int] | None = None, *, task_group_id: str | None = None, jailbreak_dataset_ids: list[int] | None = None, poc_progress_callback: Callable[[int, int, int], None] | None = None, force_refresh: bool = False) -> dict:
        """执行静态自检测算法 (Algorithm 1)

        Args:
            task_group_id: 可选，复用已有的任务组ID而非创建新的
            poc_progress_callback: 可选，PoC 池构建进度回调 (processed, total, found)
        """
        ...

    async def run_dynamic_detection(
        self, model_id: str, user_id: str, static_result: dict, max_iterations: int = 3
    ) -> dict:
        """执行动态自检测算法 (Algorithm 2)"""
        ...

    async def judge_compliance(self, model_id: str, model_output: str, judge_template: str) -> str:
        """对被测大模型单次响应做合规判断"""
        ...

    async def write_result(
        self, report_id: str, risk_subclass: str, model_output: str, compliance_result: str
    ) -> str:
        """将单条检测结果写入检测结果数据库"""
        ...
