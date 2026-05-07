"""SDPJDetector 接口定义

被依赖模块: StateScheduler
"""
from typing import Callable, Protocol, Optional

from sdpj.core.sdpj_detector.static_detector import LLMCallCallback
from sdpj.core.sdpj_detector.dynamic_detector import DynamicProgressCallback


class SDPJDetectorInterface(Protocol):
    """SDPJ 检测内核接口"""

    async def run_static_detection(self, model_id: str, user_id: str, dataset_ids: list[int] | None = None, *, task_group_id: str | None = None, jailbreak_dataset_ids: list[int] | None = None, poc_progress_callback: Callable[[int, int, int, dict, dict | None], None] | None = None, force_refresh: bool = False, llm_callback: LLMCallCallback | None = None) -> dict:
        """执行静态自检测算法 (Algorithm 1)

        Args:
            task_group_id: 可选，复用已有的任务组ID而非创建新的
            poc_progress_callback: 可选，PoC 池构建进度回调 (processed, total, found, score_counts, subtype_stats)
            llm_callback: 可选，LLM 调用回调 (request_info, response_info)
        """
        ...

    async def run_dynamic_detection(
        self, model_id: str, user_id: str, static_result: dict, max_iterations: int = 3, llm_callback: LLMCallCallback | None = None, dynamic_progress_callback: DynamicProgressCallback | None = None
    ) -> dict:
        """执行动态自检测算法 (Algorithm 2)

        Args:
            llm_callback: 可选，LLM 调用回调 (request_info, response_info)
            dynamic_progress_callback: 可选，动态检测进度回调 (processed, total, avg_iterations)
        """
        ...

    async def judge_compliance(self, model_id: str, model_output: str, judge_template: str) -> str:
        """对被测大模型单次响应做合规判断"""
        ...

    async def write_result(
        self, report_id: str, risk_subclass: str, model_output: str, compliance_result: str
    ) -> str:
        """将单条检测结果写入检测结果数据库"""
        ...
