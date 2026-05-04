"""动态检测器 - SDPJ Algorithm 2 实现"""
from datetime import datetime

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_service_interface import LLMServiceInterface, LLMError

from . import prompt_builder, result_parser
from .static_detector import _call_llm


async def run_dynamic_detection(
    llm: LLMServiceInterface,
    data_processor: DataProcessorInterface,
    model_id: str,
    user_id: str,
    static_result: dict,
    max_iterations: int = 3,
) -> dict:
    """执行动态检测算法 (Algorithm 2)

    Args:
        static_result: run_static_detection 的返回值
        max_iterations: 最大迭代变异次数
    """
    best_poc = static_result.get("best_poc")
    judge_template = static_result.get("judge_template")
    static_tg_id = static_result.get("task_group_id")

    if not best_poc or not static_tg_id:
        return {"status": "no_static_base", "task_group_id": None}

    attack_template = prompt_builder.build_attack_template(best_poc)
    task_group_id = await data_processor.create_task_group(user_id, model_id)
    instance = await llm.get_service_instance(model_id)

    static_agg = await data_processor.aggregate_task_group_results(static_tg_id)

    for task in static_agg.get("tasks", []):
        report = task.get("report")
        if not report:
            continue

        ds_id = task.get("dataset_id", "0")
        dyn_task_id = await data_processor.create_detection_task(
            task_group_id, int(ds_id), "running", datetime.now()
        )
        dyn_report_id = await data_processor.create_detection_report(dyn_task_id)

        for rd in report.get("result_data", []):
            if rd.get("compliance_result") != "合规":
                await data_processor.append_result_data(
                    dyn_report_id,
                    rd.get("risk_subclass", ""),
                    rd.get("model_output", ""),
                    rd.get("compliance_result", "违规"),
                )
                continue

            subtype = rd.get("risk_subclass", "")
            current_poc = rd.get("model_output", "")
            final_output = current_poc
            final_judgment = "合规"

            for _ in range(max_iterations):
                try:
                    mut_input = prompt_builder.build_mutation_input(attack_template, current_poc, final_output)
                    mut_resp = await _call_llm(llm, instance, "", mut_input)
                    mutated_poc = result_parser.extract_model_output(mut_resp)

                    resp = await _call_llm(llm, instance, "", mutated_poc)
                    output_text = result_parser.extract_model_output(resp)

                    judge_input = prompt_builder.build_judge_input(judge_template, output_text)
                    judge_resp = await _call_llm(llm, instance, "", judge_input)
                    judgment = result_parser.parse_compliance_judgment(judge_resp)

                    final_output = output_text
                    final_judgment = judgment
                    current_poc = mutated_poc

                    if judgment == "违规":
                        break
                except LLMError:
                    final_judgment = "违规"
                    break

            await data_processor.append_result_data(
                dyn_report_id, subtype, final_output, final_judgment
            )

        await data_processor.update_task_status(dyn_task_id, "completed", datetime.now())

    return {"status": "completed", "task_group_id": task_group_id}
