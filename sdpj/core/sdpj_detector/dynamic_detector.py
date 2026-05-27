"""动态检测器 - SDPJ Algorithm 2 实现."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_service_interface import LLMError, LLMServiceInterface
from sdpj.infrastructure.utils import encoding as encoding_utils
from sdpj.infrastructure.utils.rate_limiter import RateLimiter

from . import prompt_builder, result_parser
from .static_detector import _BATCH_SIZE, LLMCallCallback, _call_llm

DynamicProgressCallback = Callable[[int, int, float, dict | None], None]


async def run_dynamic_detection(  # noqa: C901, D417, PLR0913, PLR0915
    llm: LLMServiceInterface,
    data_processor: DataProcessorInterface,
    model_id: str,
    user_id: str,
    static_result: dict,
    max_iterations: int = 3,
    max_rps: float = 5.0,
    max_concurrency: int = 10,
    llm_callback: LLMCallCallback | None = None,
    dynamic_progress_callback: DynamicProgressCallback | None = None,
    encoding_type: str | None = None,
) -> dict:
    """执行动态检测算法 (Algorithm 2).

    Args:
        static_result: run_static_detection 的返回值
        max_iterations: 最大迭代变异次数
        dynamic_progress_callback: 动态检测进度回调 (processed, total, avg_iterations)

    """
    poc_pool = static_result.get("poc_pool")
    judge_template = static_result.get("judge_template")
    static_tg_id = static_result.get("task_group_id")

    if not poc_pool or not static_tg_id:
        return {"status": "no_static_base", "task_group_id": None}

    attack_template = prompt_builder.build_attack_template(poc_pool[0])
    task_group_id = static_tg_id
    instance = await llm.get_service_instance(model_id)
    limiter = RateLimiter(max_rps=max_rps)
    sem = asyncio.Semaphore(max_concurrency)

    static_agg = await data_processor.aggregate_task_group_results(static_tg_id)

    total_compliant = 0
    for task in static_agg.get("tasks", []):
        report = task.get("report")
        if not report:
            continue
        for rd in report.get("result_data", []):
            if rd.get("compliance_result") == "合规":
                total_compliant += 1

    iteration_total = total_compliant * len(poc_pool) * max_iterations
    iteration_breakdown = {
        "compliant": total_compliant,
        "poc_count": len(poc_pool),
        "max_iters": max_iterations,
    }
    total_iterations = 0

    for task in static_agg.get("tasks", []):
        report = task.get("report")
        if not report:
            continue

        ds_id = task.get("dataset_id", "0")
        dyn_task_id = await data_processor.create_detection_task(
            task_group_id, int(ds_id), "running", datetime.now(UTC),
            algorithm_type="dynamic",
        )
        dyn_report_id = await data_processor.create_detection_report(dyn_task_id)

        non_compliant_entries = []
        compliant_rds = []
        for rd in report.get("result_data", []):
            if rd.get("compliance_result") != "合规":
                non_compliant_entries.append(
                    {
                        "risk_subclass": rd.get("risk_subclass", ""),
                        "poc": rd.get("poc", ""),
                        "model_output": rd.get("model_output", ""),
                        "compliance_result": rd.get("compliance_result", "违规"),
                        "iteration_count": 0,
                    },
                )
            else:
                compliant_rds.append(rd)

        async def _process_compliant(rd, _sem=sem, _limiter=limiter):  # noqa: ANN001, ANN202
            subtype = rd.get("risk_subclass", "")
            current_poc = rd.get("poc", "")
            final_output = rd.get("model_output", "")
            final_judgment = "合规"
            sample_iterations = 0

            async with _sem:
                for poc in poc_pool:
                    iter_poc = poc
                    iter_output = final_output
                    for _ in range(max_iterations):
                        sample_iterations += 1
                        try:
                            mut_input = prompt_builder.build_mutation_input(
                                attack_template, iter_poc, iter_output,
                            )
                            mut_resp = await _call_llm(
                                llm, instance, "", mut_input, _limiter, llm_callback,
                            )
                            mutated_poc = result_parser.extract_model_output(mut_resp)

                            send_poc = mutated_poc
                            if encoding_type is not None:
                                send_poc = encoding_utils.build_encoded_injection_sample(
                                    mutated_poc, encoding_type,
                                )

                            resp = await _call_llm(
                                llm, instance, "", send_poc, _limiter, llm_callback,
                            )
                            output_text = result_parser.extract_model_output(resp)

                            judge_input = prompt_builder.build_judge_input(
                                judge_template, output_text,
                            )
                            judge_resp = await _call_llm(
                                llm, instance, "", judge_input, _limiter, llm_callback,
                            )
                            judgment = result_parser.parse_compliance_judgment(judge_resp)

                            iter_output = output_text
                            iter_poc = mutated_poc
                            final_output = output_text
                            final_judgment = judgment
                            current_poc = mutated_poc

                            if judgment == "违规":
                                break
                        except LLMError:
                            final_judgment = "合规"
                            break
                    if final_judgment == "违规":
                        break

            return {
                "risk_subclass": subtype,
                "poc": current_poc,
                "model_output": final_output,
                "compliance_result": final_judgment,
                "iteration_count": sample_iterations,
            }

        compliant_results = []

        async def _process_compliant_tracked(rd):  # noqa: ANN001, ANN202
            nonlocal total_iterations
            result = await _process_compliant(rd)
            total_iterations += result["iteration_count"]
            if dynamic_progress_callback is not None:
                avg_iter = (
                    round(total_iterations / max(iteration_total, 1), 2)
                    if total_iterations
                    else 0.0
                )
                dynamic_progress_callback(total_iterations, iteration_total, avg_iter, iteration_breakdown)
            return result

        for batch_start in range(0, len(compliant_rds), _BATCH_SIZE):
            batch = compliant_rds[batch_start : batch_start + _BATCH_SIZE]
            results = await asyncio.gather(*[_process_compliant_tracked(rd) for rd in batch])
            compliant_results.extend(results)

        batch_entries = non_compliant_entries + compliant_results
        if batch_entries:
            await data_processor.clear_result_data_by_report(dyn_report_id)
            await data_processor.append_result_data_batch(dyn_report_id, batch_entries)

        await data_processor.update_task_status(
            dyn_task_id, "completed", datetime.now(UTC),
        )

    avg_iteration_count = (
        round(total_iterations / max(iteration_total, 1), 2) if total_iterations else 0.0
    )
    return {
        "status": "completed",
        "task_group_id": task_group_id,
        "avg_iteration_count": avg_iteration_count,
    }
