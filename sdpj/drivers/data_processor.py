"""DataProcessor 检测数据处理模块实现

负责检测样本与数据集的查询维护、检测结果持久化、报告数据汇总、
多模态与多编码样本构造及响应处理、文件导入及结构化数据序列化。

依赖模块：SampleDB, ResultDB, UtilsLib
被依赖模块：SDPJDetector, PrivateConfigManager, ReportManager
"""

from typing import Optional, Literal, Any, Union
from pathlib import Path
from datetime import datetime

from sdpj.infrastructure.database.sample_db.interface import SampleDBInterface
from sdpj.infrastructure.database.result_db.interface import ResultDBInterface
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
                "risk_type": ds["risk_type"]
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
        # 按风险类型筛选数据集
        datasets = await self._sample_db.get_datasets_by_risk_type(risk_type)

        result = []
        for dataset in datasets:
            dataset_id = dataset["dataset_id"]
            # 加载该数据集的所有样本
            samples = await self._sample_db.get_samples_by_dataset(dataset_id)

            result.append({
                "dataset_id": dataset_id,
                "dataset_name": dataset["name"],
                "samples": [
                    {
                        "sample_id": sample["sample_id"],
                        "subtype": sample["subtype"],
                        "poc": sample["poc"]
                    }
                    for sample in samples
                ]
            })

        return result

    async def import_private_dataset(
        self,
        name: str,
        risk_type: str,
        samples: list[dict]
    ) -> dict:
        """导入用户私有数据集

        Args:
            name: 数据集名称
            risk_type: 安全风险类型
            samples: 样本条目清单

        Returns:
            导入结果字典
        """
        # 创建数据集
        dataset_id = await self._sample_db.create_dataset(name, risk_type)

        # 批量添加样本
        sample_ids = []
        for sample in samples:
            sample_id = await self._sample_db.add_sample(
                subtype=sample["subtype"],
                poc=sample["poc"],
                dataset_id=dataset_id
            )
            sample_ids.append(sample_id)

        return {
            "dataset_id": dataset_id,
            "sample_ids": sample_ids
        }

    async def remove_dataset(self, dataset_id: int) -> bool:
        """移除私有数据集

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果
        """
        return await self._sample_db.delete_dataset(dataset_id)

    # ==================== 检测结果的持久化 ====================

    async def create_task_group(
        self,
        user_id: str,
        model_id: str
    ) -> str:
        """开设检测任务组"""
        await self._result_db.register_target_model(model_id)
        task_group_id = await self._result_db.create_task_group(user_id, model_id)
        return task_group_id

    async def create_detection_task(
        self,
        task_group_id: str,
        dataset_id: int,
        task_status: str,
        start_time: datetime
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
        # 将 dataset_id 转换为字符串以符合 ResultDB 接口
        task_id = await self._result_db.create_detection_task(
            task_group_id=task_group_id,
            dataset_id=str(dataset_id),
            task_status=task_status,
            start_time=start_time
        )
        return task_id

    async def update_task_status(
        self,
        task_id: str,
        task_status: str,
        end_time: Optional[datetime] = None
    ) -> bool:
        """更新检测子任务状态

        Args:
            task_id: 任务 ID
            task_status: 任务状态
            end_time: 结束时间

        Returns:
            更新结果
        """
        return await self._result_db.update_task_status(
            task_id=task_id,
            task_status=task_status,
            end_time=end_time
        )

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
        model_output: str,
        compliance_result: str
    ) -> str:
        """追加单条检测结果数据

        Args:
            report_id: 检测报告 ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果

        Returns:
            新创建结果条目的结果数据 ID
        """
        return await self._result_db.append_result_data(
            report_id=report_id,
            risk_subclass=risk_subclass,
            model_output=model_output,
            compliance_result=compliance_result
        )

    # ==================== 检测报告数据的汇总与产出 ====================

    async def aggregate_task_group_results(self, task_group_id: str) -> dict:
        """汇总任务组下全部检测明细

        Args:
            task_group_id: 任务组 ID

        Returns:
            任务组 → 任务 → 报告 → 结果明细的结构化数据
        """
        # 获取任务组信息
        task_group = await self._result_db.get_task_group(task_group_id)

        # 获取任务组下的所有任务
        tasks = await self._result_db.list_tasks_by_group(task_group_id)

        # 为每个任务获取报告和结果数据
        tasks_with_reports = []
        for task in tasks:
            task_id = task["task_id"]

            # 获取任务对应的报告
            report = await self._result_db.get_report_by_task(task_id)

            if report:
                # 获取报告的结果数据
                result_data = await self._result_db.list_result_data_by_report(
                    report["report_id"]
                )

                tasks_with_reports.append({
                    "task_id": task_id,
                    "dataset_id": task["dataset_id"],
                    "task_status": task["task_status"],
                    "start_time": task["start_time"],
                    "end_time": task.get("end_time"),
                    "report": {
                        "report_id": report["report_id"],
                        "result_data": result_data
                    }
                })
            else:
                # 任务没有报告
                tasks_with_reports.append({
                    "task_id": task_id,
                    "dataset_id": task["dataset_id"],
                    "task_status": task["task_status"],
                    "start_time": task["start_time"],
                    "end_time": task.get("end_time"),
                    "report": None
                })

        return {
            "task_group_id": task_group_id,
            "user_id": task_group["user_id"],
            "model_id": task_group["model_id"],
            "tasks": tasks_with_reports
        }

    async def list_task_groups(
        self,
        user_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> list[dict]:
        """查询检测任务组清单

        Args:
            user_id: 用户 ID 过滤条件
            model_id: 模型 ID 过滤条件

        Returns:
            任务组元信息列表
        """
        return await self._result_db.list_task_groups(
            user_id=user_id,
            model_id=model_id
        )

    async def list_detection_reports(
        self,
        task_group_id: Optional[str] = None
    ) -> list[dict]:
        """查询检测报告清单

        Args:
            task_group_id: 任务组 ID 过滤条件

        Returns:
            报告元信息列表
        """
        return await self._result_db.list_detection_reports(
            task_group_id=task_group_id
        )

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

    async def export_report_file(
        self,
        report_data: dict,
        target_format: Literal["json", "yaml"]
    ) -> str:
        content = (
            self._utils.serialize_json(report_data)
            if target_format == "json"
            else self._utils.serialize_yaml(report_data)
        )
        task_group_id = report_data.get("task_group_id", "unknown")
        export_dir = Path("data/reports/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{task_group_id}.{target_format}"
        self._utils.write_file(str(path), content)
        return str(path)

    # ==================== 多模态与多编码的样本构造及响应处理 ====================

    def construct_multimodal_sample(
        self,
        poc: str,
        target_modality: Literal["image", "audio", "video"]
    ) -> bytes:
        if target_modality == "image":
            return self._utils.text_to_image(poc)
        if target_modality == "audio":
            return self._utils.text_to_audio(poc)
        if target_modality == "video":
            return self._utils.text_to_video(poc)
        raise NotImplementedError(f"模态 '{target_modality}' 暂未支持")

    def parse_multimodal_response(
        self,
        response_data: bytes,
        source_modality: Literal["image", "audio", "video"]
    ) -> str:
        if source_modality == "image":
            return self._utils.image_to_text(response_data)
        if source_modality == "audio":
            return self._utils.audio_to_text(response_data)
        if source_modality == "video":
            return self._utils.video_to_text(response_data)
        raise NotImplementedError(f"模态 '{source_modality}' 暂未支持")

    def construct_encoded_sample(
        self,
        poc: str,
        encoding_type: Literal["base64", "url", "unicode_escape", "hex"]
    ) -> str:
        return self._utils.encode_text(poc, encoding_type)

    def decode_response_content(
        self,
        encoded_content: str,
        encoding_type: Literal["base64", "url", "unicode_escape", "hex"]
    ) -> str:
        return self._utils.decode_text(encoded_content, encoding_type)

    # ==================== 文件导入及结构化数据序列化 ====================

    def read_file(
        self,
        file_path: Union[Path, str],
        mode: Literal["text", "binary"] = "text"
    ) -> Union[str, bytes]:
        return self._utils.read_file(str(file_path), mode)

    def validate_file_format(
        self,
        content: Union[str, bytes],
        expected_format: Literal["csv", "json", "yaml"],
    ) -> tuple[bool, str]:
        text = content if isinstance(content, str) else content.decode("utf-8")
        return self._utils.validate_file_format(text, expected_format)

    def serialize_data(
        self,
        data: Any,
        format: Literal["json", "yaml"]
    ) -> str:
        if format == "json":
            return self._utils.serialize_json(data)
        return self._utils.serialize_yaml(data)

    def deserialize_data(
        self,
        serialized_data: str,
        format: Literal["json", "yaml"]
    ) -> Any:
        if format == "json":
            return self._utils.deserialize_json(serialized_data)
        return self._utils.deserialize_yaml(serialized_data)
