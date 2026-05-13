"""DataProcessor 检测数据处理模块实现

负责检测样本与数据集的查询维护、检测结果持久化、报告数据汇总、
多模态与多编码样本构造及响应处理、文件导入及结构化数据序列化。

依赖模块：SampleDB, ResultDB, UtilsLib
被依赖模块：SDPJDetector, PrivateConfigManager, ReportManager
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional, Union

from sdpj.infrastructure.database.result_db.interface import ResultDBInterface
from sdpj.infrastructure.database.sample_db.interface import SampleDBInterface
from sdpj.infrastructure.utils.utils_interface import UtilsInterface


class DataProcessor:
    """检测数据处理模块实现类"""

    def __init__(
        self,
        sample_db: SampleDBInterface,
        result_db: ResultDBInterface,
        utils_lib: UtilsInterface,
    ):
        self._sample_db = sample_db
        self._result_db = result_db
        self._utils = utils_lib

    # ==================== 检测样本与数据集的查询与维护 ====================

    async def get_all_datasets(self) -> list[dict]:
        """查询检测数据集清单

        Returns:
            全部数据集元信息列表
        """
        datasets = await self._sample_db.get_all_datasets()
        return [
            {
                "dataset_id": ds["dataset_id"],
                "name": ds["name"],
                "risk_type": ds["risk_type"],
                "resource_id": ds.get("resource_id"),
                "created_at": ds.get("created_at"),
                "sample_count": ds.get("sample_count", 0),
            }
            for ds in datasets
        ]

    async def load_dataset_by_risk_type(self, risk_type: str) -> list[dict]:
        """按安全风险类型加载数据集样本

        Args:
            risk_type: 安全风险类型

        Returns:
            对应数据集及其全部样本列表
        """
        datasets = await self._sample_db.get_datasets_by_risk_type(risk_type)
        all_samples = await self._sample_db.get_samples_by_risk_type(risk_type)

        samples_by_dataset: dict[int, list[dict]] = {}
        for sample in all_samples:
            ds_id = sample["dataset_id"]
            samples_by_dataset.setdefault(ds_id, []).append(
                {
                    "sample_id": sample["sample_id"],
                    "subtype": sample["subtype"],
                    "poc": sample["poc"],
                }
            )

        result = []
        for dataset in datasets:
            dataset_id = dataset["dataset_id"]
            result.append(
                {
                    "dataset_id": dataset_id,
                    "dataset_name": dataset["name"],
                    "samples": samples_by_dataset.get(dataset_id, []),
                }
            )

        return result

    async def import_private_dataset(
        self, name: str, risk_type: str, samples: list[dict], resource_id: int | None = None
    ) -> dict:
        """导入用户私有数据集

        Args:
            name: 数据集名称
            risk_type: 安全风险类型
            samples: 样本条目清单
            resource_id: 对应 UserDB Resource 表的 resource_id

        Returns:
            导入结果字典
        """
        # 创建数据集
        dataset_id = await self._sample_db.create_dataset(name, risk_type, resource_id)

        # 批量添加样本
        sample_ids = []
        for sample in samples:
            sample_id = await self._sample_db.add_sample(
                subtype=sample["subtype"], poc=sample["poc"], dataset_id=dataset_id
            )
            sample_ids.append(sample_id)

        return {"dataset_id": dataset_id, "sample_ids": sample_ids}

    async def remove_dataset(self, dataset_id: int) -> bool:
        """移除私有数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果
        """
        return await self._sample_db.delete_dataset(dataset_id)

    async def add_dataset_record(
        self, name: str, sample_count: int, file_path: str, risk_type: str = "custom", resource_id: int | None = None
    ) -> int:
        """添加数据集记录到数据库

        Args:
            name: 数据集名称
            sample_count: 样本数量
            file_path: 文件路径
            risk_type: 安全风险类型
            resource_id: 对应 UserDB Resource 表的 resource_id

        Returns:
            数据集 ID
        """
        dataset_id = await self._sample_db.create_dataset(name=name, risk_type=risk_type, resource_id=resource_id)

        import json
        from pathlib import Path

        p = Path(file_path)
        if p.exists() and p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                subtype = data.get("subtype", "unknown")
                                poc = data.get("poc", "")
                                if poc:
                                    await self._sample_db.add_sample(subtype=subtype, poc=poc, dataset_id=dataset_id)
                            except json.JSONDecodeError:
                                continue
            except Exception:
                pass

        return dataset_id

    # ==================== 检测结果的持久化 ====================

    async def register_target_model(self, model_id: str) -> dict:
        """登记被测大模型（幂等）"""
        return await self._result_db.register_target_model(model_id)

    async def create_task_group(self, user_id: str, model_id: str) -> str:
        """开设检测任务组（若被测大模型未登记则先行入表）"""
        await self._result_db.register_target_model(model_id)
        task_group_id = await self._result_db.create_task_group(int(user_id), model_id)
        print(f"[DEBUG DataProcessor] create_task_group: user_id={user_id}, model_id={model_id} -> {task_group_id}", flush=True)
        return task_group_id

    async def create_task_group_with_id(self, task_group_id: str, user_id: str, model_id: str) -> str:
        """以指定ID开设检测任务组（幂等，内部已处理重复注册）"""
        print(f"[DEBUG DataProcessor] create_task_group_with_id: task_group_id={task_group_id}, user_id={user_id}, model_id={model_id}", flush=True)
        result = await self._result_db.create_task_group_with_id(task_group_id, int(user_id), model_id)
        print(f"[DEBUG DataProcessor] create_task_group_with_id DONE: {result}", flush=True)
        return result

    async def create_detection_task(
        self, task_group_id: str, dataset_id: int, task_status: str, start_time: datetime
    ) -> str:
        """创建检测子任务

        Args:
            task_group_id: 任务组 ID
            dataset_id: 数据集 ID
            task_status: 初始任务状态
            start_time: 开始时间

        Returns:
            新创建任务的任务 ID
        """
        print(f"[DEBUG DataProcessor] create_detection_task: task_group_id={task_group_id}, dataset_id={dataset_id}, task_status={task_status}", flush=True)
        # 将 dataset_id 转换为字符串以符合 ResultDB 接口
        task_id = await self._result_db.create_detection_task(
            task_group_id=task_group_id, dataset_id=dataset_id, task_status=task_status, start_time=start_time
        )
        return task_id

    async def update_task_status(self, task_id: str, task_status: str, end_time: Optional[datetime] = None) -> bool:
        """更新检测子任务状态

        Args:
            task_id: 任务 ID
            task_status: 任务状态
            end_time: 结束时间

        Returns:
            更新结果
        """
        return await self._result_db.update_task_status(task_id=task_id, task_status=task_status, end_time=end_time)

    async def create_detection_report(self, task_id: str) -> str:
        """创建检测报告条目

        Args:
            task_id: 所属任务 ID

        Returns:
            新创建报告的检测报告 ID
        """
        return await self._result_db.create_detection_report(task_id)

    async def append_result_data(
        self,
        report_id: str,
        risk_subclass: str,
        poc: str,
        model_output: str,
        compliance_result: str,
        iteration_count: Optional[int] = None,
    ) -> str:
        """追加单条检测结果数据

        Args:
            report_id: 检测报告 ID
            risk_subclass: 风险具体子类
            poc: 原始PoC
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果
            iteration_count: 动态检测迭代次数（可选）

        Returns:
            新创建结果条目的结果数据 ID
        """
        return await self._result_db.append_result_data(
            report_id=report_id,
            risk_subclass=risk_subclass,
            poc=poc,
            model_output=model_output,
            compliance_result=compliance_result,
            iteration_count=iteration_count,
        )

    async def append_result_data_batch(
        self,
        report_id: str,
        entries: list[dict],
    ) -> list[str]:
        return await self._result_db.append_result_data_batch(report_id, entries)

    # ==================== 检测报告数据的汇总与产出 ====================

    async def aggregate_task_group_results(self, task_group_id: str, task_id: str | None = None) -> dict:
        """汇总任务组下全部检测明细

        Args:
            task_group_id: 任务组 ID
            task_id: 可选，仅汇总指定任务的数据

        Returns:
            任务组 → 任务 → 报告 → 结果明细的结构化数据
        """
        task_group = await self._result_db.get_task_group(task_group_id)

        if task_id:
            tasks = [t for t in await self._result_db.list_tasks_by_group(task_group_id) if t["task_id"] == task_id]
        else:
            tasks = await self._result_db.list_tasks_by_group(task_group_id)

        reports = await self._result_db.list_reports_by_task_group(task_group_id)
        report_by_task = {r["task_id"]: r for r in reports}

        report_ids = [r["report_id"] for r in reports if r.get("report_id")]
        all_result_data = await self._result_db.list_result_data_by_reports(report_ids) if report_ids else []
        result_data_by_report: dict[str, list[dict]] = {}
        for rd in all_result_data:
            rid = rd["report_id"]
            result_data_by_report.setdefault(rid, []).append(rd)

        tasks_with_reports = []
        for task in tasks:
            tid = task["task_id"]
            report = report_by_task.get(tid)
            if report:
                tasks_with_reports.append(
                    {
                        "task_id": tid,
                        "dataset_id": task["dataset_id"],
                        "task_status": task["task_status"],
                        "start_time": task["start_time"],
                        "end_time": task.get("end_time"),
                        "report": {
                            "report_id": report["report_id"],
                            "result_data": result_data_by_report.get(report["report_id"], []),
                        },
                    }
                )
            else:
                tasks_with_reports.append(
                    {
                        "task_id": tid,
                        "dataset_id": task["dataset_id"],
                        "task_status": task["task_status"],
                        "start_time": task["start_time"],
                        "end_time": task.get("end_time"),
                        "report": None,
                    }
                )

        return {
            "task_group_id": task_group_id,
            "user_id": task_group["user_id"],
            "model_id": task_group["model_id"],
            "tasks": tasks_with_reports,
        }

    async def list_task_groups(self, user_id: Optional[str] = None, model_id: Optional[str] = None) -> list[dict]:
        """查询检测任务组清单

        Args:
            user_id: 用户 ID 过滤条件
            model_id: 模型 ID 过滤条件

        Returns:
            任务组元信息列表
        """
        return await self._result_db.list_task_groups(user_id=int(user_id) if user_id else None, model_id=model_id)

    async def list_reports_summary(self, user_id: Optional[str] = None, model_id: Optional[str] = None) -> list[dict]:
        summaries = await self._result_db.compute_reports_summary(
            user_id=int(user_id) if user_id else None, model_id=model_id
        )
        dataset_ids = set()
        for group in summaries:
            for child in group.get("children", []):
                ds_id = child.get("dataset_id")
                if ds_id is not None:
                    dataset_ids.add(ds_id)
        if dataset_ids:
            ds_name_map = {}
            for ds_id in dataset_ids:
                ds_info = await self._sample_db.get_dataset_by_id(ds_id)
                if ds_info:
                    ds_name_map[ds_id] = ds_info.get("name", str(ds_id))
            for group in summaries:
                for child in group.get("children", []):
                    ds_id = child.get("dataset_id")
                    if ds_id is not None and ds_id in ds_name_map:
                        child["dataset_name"] = ds_name_map[ds_id]
        return summaries

    async def list_detection_reports(self, task_group_id: Optional[str] = None) -> list[dict]:
        """查询检测报告清单

        Args:
            task_group_id: 任务组 ID 过滤条件

        Returns:
            报告元信息列表
        """
        return await self._result_db.list_detection_reports(task_group_id=task_group_id)

    async def delete_task_group(self, task_group_id: str) -> bool:
        """删除检测任务组及其关联结果

        Args:
            task_group_id: 任务组 ID

        Returns:
            删除结果
        """
        return await self._result_db.delete_task_group(task_group_id)

    async def delete_detection_task(self, task_id: str) -> bool:
        """删除检测任务及其关联结果

        Args:
            task_id: 任务 ID

        Returns:
            删除结果
        """
        return await self._result_db.delete_detection_task(task_id)

    async def delete_detection_report(self, report_id: str) -> bool:
        """删除检测报告及其关联结果

        Args:
            report_id: 检测报告 ID

        Returns:
            删除结果
        """
        return await self._result_db.delete_detection_report(report_id)

    async def delete_result_data(self, result_data_id: str) -> bool:
        """删除检测结果数据条目

        Args:
            result_data_id: 结果数据 ID

        Returns:
            删除结果
        """
        return await self._result_db.delete_result_data(result_data_id)

    async def resolve_task_group_id(
        self,
        task_group_id: Optional[str] = None,
        task_id: Optional[str] = None,
        report_id: Optional[str] = None,
        result_data_id: Optional[str] = None,
    ) -> Optional[str]:
        if task_group_id:
            return task_group_id
        if task_id:
            try:
                task = await self._result_db.get_detection_task(task_id)
                return task.get("task_group_id")
            except ValueError:
                return None
        if report_id:
            try:
                report = await self._result_db.get_detection_report(report_id)
                tid = report.get("task_id")
                if tid:
                    task = await self._result_db.get_detection_task(tid)
                    return task.get("task_group_id")
            except ValueError:
                return None
        if result_data_id:
            try:
                rd = await self._result_db.get_result_data(result_data_id)
                if rd:
                    report = await self._result_db.get_detection_report(rd["report_id"])
                    tid = report.get("task_id")
                    if tid:
                        task = await self._result_db.get_detection_task(tid)
                        return task.get("task_group_id")
            except (ValueError, Exception):
                return None
        return None

    async def count_compliance_results(self) -> dict[str, int]:
        return await self._result_db.count_compliance_results()

    async def export_report_file(
        self, report_data: dict, target_format: Literal["json", "yaml", "jsonl"]
    ) -> tuple[str, str]:
        if target_format == "jsonl":
            lines = []
            for task in report_data.get("tasks", []):
                report = task.get("report")
                if report and report.get("result_data"):
                    for r in report["result_data"]:
                        lines.append(self._utils.serialize_json(r))
            content = "\n".join(lines)
        elif target_format == "json":
            content = self._utils.serialize_json(report_data)
        else:
            content = self._utils.serialize_yaml(report_data)
        task_group_id = report_data.get("task_group_id", "unknown")
        filename = f"{task_group_id}.{target_format}"
        return filename, content

    # ==================== 多模态与多编码的样本构造及响应处理 ====================

    def construct_multimodal_sample(self, poc: str, target_modality: Literal["image", "audio", "video"]) -> bytes:
        if target_modality == "image":
            return self._utils.text_to_image(poc)
        if target_modality == "audio":
            return self._utils.text_to_audio(poc)
        if target_modality == "video":
            return self._utils.text_to_video(poc)
        raise NotImplementedError(f"模态 '{target_modality}' 暂未支持")

    def parse_multimodal_response(
        self, response_data: bytes, source_modality: Literal["image", "audio", "video"]
    ) -> str:
        if source_modality == "image":
            return self._utils.image_to_text(response_data)
        if source_modality == "audio":
            return self._utils.audio_to_text(response_data)
        if source_modality == "video":
            return self._utils.video_to_text(response_data)
        raise NotImplementedError(f"模态 '{source_modality}' 暂未支持")

    def construct_encoded_sample(
        self, poc: str, encoding_type: Literal["base64", "url", "unicode_escape", "hex"]
    ) -> str:
        return self._utils.encode_text(poc, encoding_type)

    def decode_response_content(
        self, encoded_content: str, encoding_type: Literal["base64", "url", "unicode_escape", "hex"]
    ) -> str:
        return self._utils.decode_text(encoded_content, encoding_type)

    # ==================== 文件导入及结构化数据序列化 ====================

    def read_file(self, file_path: Union[Path, str], mode: Literal["text", "binary"] = "text") -> Union[str, bytes]:
        return self._utils.read_file(str(file_path), mode)

    def validate_file_format(
        self,
        content: Union[str, bytes],
        expected_format: Literal["csv", "json", "yaml"],
    ) -> tuple[bool, str]:
        text = content if isinstance(content, str) else content.decode("utf-8")
        return self._utils.validate_file_format(text, expected_format)

    def serialize_data(self, data: Any, format: Literal["json", "yaml"]) -> str:
        if format == "json":
            return self._utils.serialize_json(data)
        return self._utils.serialize_yaml(data)

    def deserialize_data(self, serialized_data: str, format: Literal["json", "yaml"]) -> Any:
        if format == "json":
            return self._utils.deserialize_json(serialized_data)
        return self._utils.deserialize_yaml(serialized_data)

    # ==================== PoC 池缓存 ====================

    async def get_poc_pool_cache(self, model_id: str) -> list[dict]:
        return await self._result_db.get_poc_pool_cache(model_id)

    async def save_poc_pool_cache(
        self,
        model_id: str,
        entries: list[dict],
        dataset_version: str,
    ) -> int:
        return await self._result_db.save_poc_pool_cache(model_id, entries, dataset_version)

    async def invalidate_poc_pool_cache(self, model_id: str) -> int:
        return await self._result_db.invalidate_poc_pool_cache(model_id)
