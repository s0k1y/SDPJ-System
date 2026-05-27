"""SDPJDetector 接口定义.

被依赖模块: StateScheduler
"""

from collections.abc import Callable
from typing import Protocol

from sdpj.core.sdpj_detector.dynamic_detector import DynamicProgressCallback
from sdpj.core.sdpj_detector.static_detector import LLMCallCallback


class SDPJDetectorInterface(Protocol):
    """SDPJ 检测内核接口."""

    async def run_static_detection(  # noqa: D417, PLR0913
        self,
        model_id: str,
        user_id: str,
        dataset_ids: list[int] | None = None,
        *,
        task_group_id: str | None = None,
        jailbreak_dataset_ids: list[int] | None = None,
        max_rps: float = 5.0,
        max_concurrency: int = 10,
        poc_progress_callback: Callable[[int, int, int, dict, dict | None], None] | None = None,
        task_progress_callback: Callable[[str, int, int], None] | None = None,
        force_refresh: bool = False,
        llm_callback: LLMCallCallback | None = None,
        encoding_type: str | None = None,
    ) -> dict:
        """执行静态自检测算法 (Algorithm 1).

        Args:
            task_group_id: 可选,复用已有的任务组ID而非创建新的
            poc_progress_callback: 可选,PoC 池构建进度回调 (processed, total, found, score_counts, subtype_stats)  # noqa: E501, E501            llm_callback: 可选, LLM 调用回调 (request_info, response_info)

        """
        ...

    async def run_dynamic_detection(  # noqa: D417, PLR0913
        self,
        model_id: str,
        user_id: str,
        static_result: dict,
        max_iterations: int = 3,
        max_rps: float = 5.0,
        max_concurrency: int = 10,
        llm_callback: LLMCallCallback | None = None,
        dynamic_progress_callback: DynamicProgressCallback | None = None,
        encoding_type: str | None = None,
        target_dataset_id: int | None = None,
    ) -> dict:
        """执行动态自检测算法 (Algorithm 2).

        Args:
            llm_callback: 可选,LLM 调用回调 (request_info, response_info)
            dynamic_progress_callback: 可选,动态检测进度回调 (processed, total, avg_iterations)
            encoding_type: 可选,编码类型,None 为直接注入

        """
        ...

    async def judge_compliance(self, model_id: str, model_output: str, judge_template: str) -> str:
        """对被测大模型单次响应做合规判断."""
        ...

    async def write_result(
        self, report_id: str, risk_subclass: str, poc: str, model_output: str, compliance_result: str,
    ) -> str:
        """将单条检测结果写入检测结果数据库."""
        ...

    async def verify_connectivity(self, service_instance, timeout: float = 30.0) -> dict:  # noqa: ANN001, ASYNC109
        """验证大模型连接性,委托给 LLMService 执行健康检查  # noqa: "latency_ms": int, "model": str, "response_preview": str}.  # noqa: E501, "status": str, D205        返回: {"success": bool, D210, E501, E501.        """
        ...
