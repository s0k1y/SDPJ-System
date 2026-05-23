"""SDPJDetector SDPJ 检测内核模块

依赖模块: DataProcessor (via DataProcessorInterface), LLMService (via LLMServiceInterface)
被依赖模块: StateScheduler
"""

from typing import Callable

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_service_interface import LLMError, LLMServiceInterface

from . import prompt_builder, result_parser
from ..sdpj_detector_interface import SDPJDetectorInterface
from .dynamic_detector import DynamicProgressCallback, run_dynamic_detection
from .static_detector import LLMCallCallback, _call_llm, run_static_detection


class SDPJDetector(SDPJDetectorInterface):
    """SDPJ 检测内核"""

    def __init__(
        self,
        data_processor: DataProcessorInterface,
        llm_service: LLMServiceInterface,
    ):
        self._data_processor = data_processor
        self._llm = llm_service

    async def run_static_detection(
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
    ) -> dict:
        return await run_static_detection(
            self._llm,
            self._data_processor,
            model_id,
            user_id,
            dataset_ids,
            task_group_id=task_group_id,
            jailbreak_dataset_ids=jailbreak_dataset_ids,
            max_rps=max_rps,
            max_concurrency=max_concurrency,
            poc_progress_callback=poc_progress_callback,
            task_progress_callback=task_progress_callback,
            force_refresh=force_refresh,
            llm_callback=llm_callback,
        )

    async def run_dynamic_detection(
        self,
        model_id: str,
        user_id: str,
        static_result: dict,
        max_iterations: int = 3,
        max_rps: float = 5.0,
        max_concurrency: int = 10,
        llm_callback: LLMCallCallback | None = None,
        dynamic_progress_callback: DynamicProgressCallback | None = None,
    ) -> dict:
        return await run_dynamic_detection(
            self._llm,
            self._data_processor,
            model_id,
            user_id,
            static_result,
            max_iterations,
            max_rps=max_rps,
            max_concurrency=max_concurrency,
            llm_callback=llm_callback,
            dynamic_progress_callback=dynamic_progress_callback,
        )

    async def judge_compliance(self, model_id: str, model_output: str, judge_template: str) -> str:
        instance = await self._llm.get_service_instance(model_id)
        judge_input = prompt_builder.build_judge_input(judge_template, model_output)
        try:
            resp = await _call_llm(self._llm, instance, "", judge_input)
            return result_parser.parse_compliance_judgment(resp)
        except LLMError:
            return "违规"

    async def write_result(
        self,
        report_id: str,
        risk_subclass: str,
        poc: str,
        model_output: str,
        compliance_result: str,
    ) -> str:
        return await self._data_processor.append_result_data(
            report_id, risk_subclass, poc, model_output, compliance_result
        )

    async def verify_connectivity(self, service_instance, timeout: float = 30.0) -> dict:
        """验证大模型连接性，委托给 LLMService 执行健康检查"""
        return await self._llm.verify_connectivity(service_instance, timeout)
