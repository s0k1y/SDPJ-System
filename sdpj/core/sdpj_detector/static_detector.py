"""静态检测器 - SDPJ Algorithm 1 实现"""
import asyncio
import base64 as _b64
from datetime import datetime
from typing import Optional

from sdpj.drivers.data_processor_interface import DataProcessorInterface
from sdpj.drivers.llm_service_interface import LLMServiceInterface
from sdpj.drivers.llm_service_interface import LLMServiceInstanceProtocol, LLMError
from sdpj.infrastructure.llm_adapters.errors import StandardizedLLMError

from . import prompt_builder, result_parser

_MODALITY_MAP = {"图像": "image", "image": "image", "音频": "audio", "audio": "audio", "视频": "video", "video": "video"}
_ENCODING_MAP = {"base64": "base64", "url": "url", "unicode": "unicode_escape", "hex": "hex", "十六进制": "hex"}

_CONCURRENCY = 10


def _prepare_poc(poc: str, subtype: str, dp: DataProcessorInterface) -> str:
    lower = subtype.lower()
    for kw, modality in _MODALITY_MAP.items():
        if kw.lower() in lower:
            try:
                raw = dp.construct_multimodal_sample(poc, modality)
                return f"[{modality.upper()}_DATA:{_b64.b64encode(raw).decode()}]"
            except NotImplementedError:
                return poc
    for kw, enc in _ENCODING_MAP.items():
        if kw in lower:
            try:
                return dp.construct_encoded_sample(poc, enc)
            except Exception:
                return poc
    return poc


async def _call_llm(llm: LLMServiceInterface, instance, system: str, user: str) -> dict:
    req = llm.assemble_request(system, user)
    return await llm.invoke_llm(instance, req)


async def select_best_poc(
    llm: LLMServiceInterface,
    data_processor: DataProcessorInterface,
    model_id: str,
    dataset_id: Optional[str] = None,
) -> Optional[str]:
    """Algorithm 1 Step 1: 遍历越狱数据集，筛选最优 PoC"""
    datasets = await data_processor.load_dataset_by_risk_type("jailbreak")
    if dataset_id is not None:
        datasets = [ds for ds in datasets if ds.get("dataset_id") == dataset_id]
    if not datasets:
        return None

    instance = await llm.get_service_instance(model_id)
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def _check(sample) -> Optional[str]:
        poc = sample.get("poc", "")
        subtype = sample.get("subtype", "")
        if not poc:
            return None
        prepared = _prepare_poc(poc, subtype, data_processor)
        async with sem:
            try:
                resp = await _call_llm(llm, instance, "", prepared)
                return poc if result_parser.is_jailbreak_success(resp) else None
            except LLMError:
                return None

    all_samples = [s for ds in datasets for s in ds.get("samples", [])]
    results = await asyncio.gather(*[_check(s) for s in all_samples])
    successful = [r for r in results if r is not None]
    return min(successful, key=len) if successful else None


async def run_static_detection(
    llm: LLMServiceInterface,
    data_processor: DataProcessorInterface,
    model_id: str,
    user_id: str,
    dataset_ids: list[int] | None = None,
) -> dict:
    """执行完整的静态检测算法 (Algorithm 1)"""
    all_datasets = await data_processor.get_all_datasets()
    non_jailbreak = [ds for ds in all_datasets if ds.get("risk_type") != "jailbreak"]
    if dataset_ids is not None:
        non_jailbreak = [ds for ds in non_jailbreak if ds["dataset_id"] in dataset_ids]

    task_group_id = await data_processor.create_task_group(user_id, model_id)

    best_poc = await select_best_poc(llm, data_processor, model_id)
    if best_poc is None:
        for ds_meta in non_jailbreak:
            task_id = await data_processor.create_detection_task(
                task_group_id, ds_meta["dataset_id"], "no_jailbreak_risk", datetime.now()
            )
            await data_processor.update_task_status(task_id, "no_jailbreak_risk", datetime.now())
        return {"status": "no_jailbreak_risk", "task_group_id": task_group_id}

    judge_template = prompt_builder.build_judge_template(best_poc)
    instance = await llm.get_service_instance(model_id)
    sem = asyncio.Semaphore(_CONCURRENCY)

    for ds_meta in non_jailbreak:
        ds_id = ds_meta["dataset_id"]
        task_id = await data_processor.create_detection_task(
            task_group_id, ds_id, "running", datetime.now()
        )
        report_id = await data_processor.create_detection_report(task_id)

        datasets = await data_processor.load_dataset_by_risk_type(ds_meta["risk_type"])
        samples = next(
            (ds.get("samples", []) for ds in datasets if ds["dataset_id"] == ds_id), []
        )

        async def _process(sample, _report_id=report_id):
            poc = sample.get("poc", "")
            subtype = sample.get("subtype", "")
            prepared = _prepare_poc(poc, subtype, data_processor)
            async with sem:
                try:
                    resp = await _call_llm(llm, instance, "", prepared)
                    output_text = result_parser.extract_model_output(resp)
                    judge_input = prompt_builder.build_judge_input(judge_template, output_text)
                    judge_resp = await _call_llm(llm, instance, "", judge_input)
                    judgment = result_parser.parse_compliance_judgment(judge_resp)
                except StandardizedLLMError as e:
                    output_text = f"[ERROR] {e.message}"
                    judgment = "违规"
            await data_processor.append_result_data(_report_id, subtype, output_text, judgment)

        await asyncio.gather(*[_process(s) for s in samples])
        await data_processor.update_task_status(task_id, "completed", datetime.now())

    return {
        "status": "completed",
        "task_group_id": task_group_id,
        "best_poc": best_poc,
        "judge_template": judge_template,
    }
