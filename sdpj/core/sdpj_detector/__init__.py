"""SDPJDetector SDPJ 检测内核模块

依赖模块: DataProcessor (via DataProcessorInterface), LLMService (via LLMServiceInterface)
被依赖模块: StateScheduler
"""
from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_service_interface import LLMServiceInterface
from sdpj.drivers.llm_types import LLMError

from .static_detector import run_static_detection, select_best_poc, _call_llm
from .dynamic_detector import run_dynamic_detection
from . import prompt_builder, result_parser

from .prompt_builder import (
    build_judge_template,
    build_attack_template,
    build_judge_input,
    build_mutation_input,
)
from .result_parser import (
    parse_compliance_judgment,
    extract_model_output,
    is_jailbreak_success,
)


class SDPJDetector:
    """SDPJ 检测内核"""

    def __init__(
        self,
        data_processor: DataProcessorInterface,
        llm_service: LLMServiceInterface,
    ):
        self._data_processor = data_processor
        self._llm = llm_service

    async def run_static_detection(self, model_id: str, user_id: str) -> dict:
        return await run_static_detection(
            self._llm, self._data_processor, model_id, user_id
        )

    async def run_dynamic_detection(
        self, model_id: str, user_id: str, static_result: dict, max_iterations: int = 3
    ) -> dict:
        return await run_dynamic_detection(
            self._llm, self._data_processor, model_id, user_id,
            static_result, max_iterations
        )

    async def judge_compliance(
        self, model_id: str, model_output: str, judge_template: str
    ) -> str:
        instance = await self._llm.get_service_instance(model_id)
        judge_input = prompt_builder.build_judge_input(judge_template, model_output)
        try:
            resp = await _call_llm(self._llm, instance, "", judge_input)
            return result_parser.parse_compliance_judgment(resp)
        except LLMError:
            return "违规"

    async def write_result(
        self, report_id: str, risk_subclass: str, model_output: str, compliance_result: str
    ) -> str:
        return await self._data_processor.append_result_data(
            report_id, risk_subclass, model_output, compliance_result
        )
