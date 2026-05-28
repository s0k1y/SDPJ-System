"""DataProcessor 接口定义.

检测数据处理模块的 Protocol 接口,定义所有对外暴露的能力.
调用方:SDPJDetector, PrivateConfigManager, ReportManager
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol


class DataProcessorInterface(Protocol):
    """DataProcessor 接口协议.

    定义检测数据处理模块的所有能力,包括:
    - 检测样本与数据集的查询与维护
    - 检测结果的持久化
    - 检测报告数据的汇总与产出
    - 文件导入及结构化数据序列化
    """

    # ==================== 检测样本与数据集的查询与维护 ====================

    async def get_all_datasets(self) -> list[dict]:
        """查询检测数据集清单.

        Returns:
            全部数据集元信息列表,每条包含:
            - dataset_id: 数据集 ID
            - name: 数据集名称
            - risk_type: 安全风险类型

        触发场景:
            用户选择要使用的检测数据集

        """
        ...

    async def load_dataset_by_risk_type(self, risk_type: str) -> list[dict]:
        """按安全风险类型加载数据集样本.

        Args:
            risk_type: 安全风险类型(如「越狱攻击」「提示词注入」「安全基准」)

        Returns:
            对应数据集及其全部样本列表,每条包含:
            - dataset_id: 数据集 ID
            - dataset_name: 数据集名称
            - samples: 样本列表,每条包含:
                - sample_id: 样本 ID
                - subtype: 风险具体子类 ST
                - poc: 漏洞概念验证数据 PoC

        触发场景:
            SDPJ 静态/动态算法在步骤 1/步骤 3 加载 D_i 的全部样本

        """
        ...

    async def import_private_dataset(
        self, name: str, risk_type: str, samples: list[dict], resource_id: int | None = None,
    ) -> dict:
        """导入用户私有数据集.

        Args:
            name: 数据集名称
            risk_type: 安全风险类型
            samples: 样本条目清单(已完成格式预校验),每条包含:
                - subtype: 风险具体子类 ST
                - poc: 漏洞概念验证数据 PoC
            resource_id: 对应 UserDB Resource 表的 resource_id

        Returns:
            导入结果字典,包含:
            - dataset_id: 新创建数据集 ID
            - sample_ids: 各新增样本 ID 列表

        触发场景:
            用户上传私有数据集

        """
        ...

    async def remove_dataset(self, dataset_id: int) -> bool:
        """移除私有数据集.

        后置条件:
            删除数据集时由下层级联清理其下全部样本

        Args:
            dataset_id: 数据集 ID

        Returns:
            删除结果

        触发场景:
            用户移除私有数据集

        """
        ...

    # ==================== 检测结果的持久化 ====================

    async def register_target_model(self, model_id: str) -> dict:
        """登记被测大模型(幂等).

        确保被测大模型在数据库中已注册,用于满足外键约束.
        已存在时直接返回,不重复创建.

        Args:
            model_id: 目标被测大模型 ID

        Returns:
            {"model_id": str}

        """
        ...

    async def create_task_group(self, user_id: str, model_id: str) -> str:
        """开设检测任务组.

        后置条件:
            若被测大模型未登记则先行入表

        Args:
            user_id: 用户 ID
            model_id: 目标被测大模型 ID

        Returns:
            新创建任务组的任务组 ID

        触发场景:
            用户启动一次检测时建立承载本次检测所有产出的顶层条目

        """
        ...

    async def create_task_group_with_id(
        self, task_group_id: str, user_id: str, model_id: str,
    ) -> str:
        """以指定ID开设检测任务组(幂等).

        Args:
            task_group_id: 预生成的任务组ID
            user_id: 用户 ID
            model_id: 目标被测大模型 ID

        Returns:
            任务组 ID

        """
        ...

    async def create_detection_task(
        self, task_group_id: str, dataset_id: int, task_status: str, start_time: datetime,
        *, algorithm_type: str = "static", metadata_json: dict | None = None,
    ) -> str:
        """创建检测子任务.

        Args:
            task_group_id: 任务组 ID
            dataset_id: 数据集 ID
            task_status: 初始任务状态
            start_time: 开始时间

        Returns:
            新创建任务的任务 ID

        触发场景:
            静态/动态算法在每个待测数据集 D_i 上各启动一次检测子任务

        """
        ...

    async def update_task_status(
        self, task_id: str, task_status: str, end_time: datetime | None = None,
    ) -> bool:
        """更新检测子任务状态.

        Args:
            task_id: 任务 ID
            task_status: 任务状态
            end_time: 结束时间(可选)

        Returns:
            更新结果

        触发场景:
            任务由「进行中」转入「完成」或「异常中断」时

        """
        ...

    async def create_detection_report(self, task_id: str) -> str:
        """创建检测报告条目.

        Args:
            task_id: 所属任务 ID

        Returns:
            新创建报告的检测报告 ID

        触发场景:
            一条检测子任务完成后为其生成对应报告条目

        """
        ...

    async def append_result_data(  # noqa: D417, PLR0913
        self,
        report_id: str,
        risk_subclass: str,
        poc: str,
        model_output: str,
        compliance_result: str,
        iteration_count: int | None = None,
    ) -> str:
        """追加单条检测结果数据.

        Args:
            report_id: 检测报告 ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果
            iteration_count: 动态检测迭代次数(可选)

        Returns:
            新创建结果条目的结果数据 ID

        触发场景:
            每完成对一条样本的检测后将模型响应与合规结论落盘

        """
        ...

    async def append_result_data_batch(
        self,
        report_id: str,
        entries: list[dict],
    ) -> list[str]:
        """批量追加检测结果数据.

        Args:
            report_id: 检测报告 ID
            entries: 结果数据列表,每条包含:
                - risk_subclass: 风险具体子类
                - poc: 原始PoC
                - model_output: 被测大模型输出内容
                - compliance_result: 合规判断结果
                - iteration_count: 动态检测迭代次数(可选)

        Returns:
            所有新创建条目的结果数据 ID 列表

        触发场景:
            一批样本检测完成后将模型响应与合规结论批量落盘

        """
        ...

    async def clear_result_data_by_report(self, report_id: str) -> int:
        """清空指定报告下的所有结果数据.

        Args:
            report_id: 检测报告 ID

        Returns:
            被删除的记录数

        触发场景:
            动态检测复用静态 task 时,先清空静态结果再写入动态结果

        """
        ...

    # ==================== 检测报告数据的汇总与产出 ====================

    async def aggregate_task_group_results(
        self, task_group_id: str, task_id: str | None = None,
    ) -> dict:
        """汇总任务组下全部检测明细.

        Args:
            task_group_id: 任务组 ID
            task_id: 可选,仅汇总指定任务的数据

        Returns:
            任务组 → 任务 → 报告 → 结果明细的结构化数据,包含:
            - task_group_id: 任务组 ID
            - user_id: 用户 ID
            - model_id: 模型 ID
            - tasks: 任务列表,每条包含:
                - task_id: 任务 ID
                - dataset_id: 数据集 ID
                - task_status: 任务状态
                - start_time: 开始时间
                - end_time: 结束时间
                - report: 检测报告,包含:
                    - report_id: 检测报告 ID
                    - result_data: 结果数据列表,每条包含:
                        - result_data_id: 结果数据 ID
                        - risk_subclass: 风险具体子类
                        - model_output: 被测大模型输出内容
                        - compliance_result: 合规判断结果

        触发场景:
            ReportManager 生成可视化检测结果报告

        """
        ...

    async def list_task_groups(
        self, user_id: str | None = None, model_id: str | None = None,
    ) -> list[dict]:
        """查询检测任务组清单.

        Args:
            user_id: 用户 ID 过滤条件(可选)
            model_id: 模型 ID 过滤条件(可选)

        Returns:
            任务组元信息列表

        触发场景:
            用户浏览历史检测

        """
        ...

    async def list_reports_summary(
        self, user_id: str | None = None, model_id: str | None = None,
    ) -> list[dict]:
        """查询检测报告列表摘要(高性能,使用 SQL 聚合查询).

        避免对每个任务组单独查询并加载全部 result_data 大文本字段,
        仅通过 2 条 SQL 聚合查询获取列表视图所需的统计数据.

        Args:
            user_id: 用户 ID 过滤条件(可选)
            model_id: 模型 ID 过滤条件(可选)

        Returns:
            任务组列表,每组包含:
            - task_group_id: 任务组 ID
            - user_id: 用户 ID
            - model_id: 模型 ID
            - compliance_rate: 合规率
            - risk_level: 风险等级
            - subtype_compliance: 子类型合规统计
            - status: 状态
            - children: 子任务摘要列表

        触发场景:
            用户浏览检测报告列表

        """
        ...

    async def list_detection_reports(self, task_group_id: str | None = None) -> list[dict]:
        """查询检测报告清单.

        Args:
            task_group_id: 任务组 ID 过滤条件(可选)

        Returns:
            报告元信息列表

        触发场景:
            用户浏览历史检测

        """
        ...

    async def delete_task_group(self, task_group_id: str) -> bool:
        """删除检测任务组及其关联结果.

        后置条件:
            按删除粒度由下层保证级联清理

        Args:
            task_group_id: 任务组 ID

        Returns:
            删除结果

        触发场景:
            用户删除检测报告

        """
        ...

    async def delete_detection_task(self, task_id: str) -> bool:
        """删除检测任务及其关联结果.

        Args:
            task_id: 任务 ID

        Returns:
            删除结果

        触发场景:
            用户删除检测报告

        """
        ...

    async def delete_detection_report(self, report_id: str) -> bool:
        """删除检测报告及其关联结果.

        Args:
            report_id: 检测报告 ID

        Returns:
            删除结果

        触发场景:
            用户精修报告内容

        """
        ...

    async def delete_result_data(self, result_data_id: str) -> bool:
        """删除检测结果数据条目.

        Args:
            result_data_id: 结果数据 ID

        Returns:
            删除结果

        触发场景:
            用户精修报告内容

        """
        ...

    async def resolve_task_group_id(
        self,
        task_group_id: str | None = None,
        task_id: str | None = None,
        report_id: str | None = None,
        result_data_id: str | None = None,
    ) -> str | None:
        """根据任意粒度目标反查所属任务组 ID.

        按优先级依次尝试:task_group_id > task_id > report_id > result_data_id,
        逐级回溯直到定位到 task_group_id.

        Args:
            task_group_id: 任务组 ID(直接返回)
            task_id: 任务 ID(通过任务反查任务组)
            report_id: 报告 ID(通过报告反查任务再反查任务组)
            result_data_id: 结果数据 ID(通过结果数据反查报告再反查任务再反查任务组)

        Returns:
            任务组 ID,无法解析时返回 None

        """
        ...

    async def count_compliance_results(self) -> dict[str, int]:
        """按合规判断结果统计数量.

        Returns:
            {compliance_result: count} 映射

        """
        ...

    async def export_report_file(
        self, report_data: dict, target_format: str,
    ) -> tuple[str, str]:
        """导出检测报告文件.

        Args:
            report_data: 已汇总的报告结构化数据
            target_format: 目标文件格式

        Returns:
            (文件名, 文件内容字符串)

        触发场景:
            用户下载检测报告

        """
        ...

    # ==================== 文件导入及结构化数据序列化 ====================

    def read_file(
        self, file_path: Path | str, mode: Literal["text", "binary"] = "text",
    ) -> str | bytes:
        """读取本地数据集/配置文件.

        Args:
            file_path: 文件路径或文件流
            mode: 读取模式(text/binary)

        Returns:
            文件内容

        触发场景:
            加载数据集文件;加载用户私有检测配置文件

        """
        ...

    def validate_file_format(
        self,
        content: str | bytes,
        expected_format: Literal["csv", "json", "yaml"],
    ) -> tuple[bool, str]:
        """预校验上传文件格式.

        Args:
            content: 文件内容
            expected_format: 期望格式(csv/json/yaml)

        Returns:
            (格式合规性判定结果, 关键错误信息)

        触发场景:
            用户上传私有数据集/私有检测配置文件时的格式预校验

        """
        ...

    def serialize_data(self, data: Any, format: Literal["json", "yaml"]) -> str:  # noqa: A002, ANN401
        """结构化数据的序列化.

        Args:
            data: 结构化对象
            format: 目标格式

        Returns:
            转换结果

        触发场景:
            跨层结构化数据的文件落盘

        """
        ...

    def deserialize_data(self, serialized_data: str, format: Literal["json", "yaml"]) -> Any:  # noqa: A002, ANN401
        """结构化数据的反序列化.

        Args:
            serialized_data: 序列化字符串
            format: 源格式

        Returns:
            转换结果

        触发场景:
            跨层结构化数据的载入

        """
        ...

    # ==================== 多编码样本构造与响应还原 ====================

    def construct_encoded_sample(self, poc: str, encoding_type: str) -> str:
        """构造多编码检测样本.

        Args:
            poc: 明文 PoC 文本
            encoding_type: 编码类型(如 base64, caesar)

        Returns:
            编码后的样本字符串

        触发场景:
            多编码间接注入检测时,将明文 PoC 变换为目标编码形式

        """
        ...

    def decode_response_content(self, encoded_content: str, encoding_type: str) -> str:
        """还原多编码响应内容.

        Args:
            encoded_content: 编码后的响应内容
            encoding_type: 编码类型

        Returns:
            还原后的明文内容

        触发场景:
            多编码间接注入检测后,将编码响应还原为明文

        """
        ...

    # ==================== 多模态样本构造 ====================

    async def build_multimodal_content(self, poc: str, modality: str) -> list[dict]:
        """构造多模态检测样本.

        将明文 PoC 变换为 OpenAI Chat Completions content 数组格式,
        变换结果仅在内存中构造,不落盘(约束七).

        Args:
            poc: 明文 PoC 文本
            modality: 目标模态,支持 jpg/png/mp3/wav

        Returns:
            OpenAI content 数组(list[dict])

        Raises:
            ValueError: 不支持的 modality

        触发场景:
            多模态间接注入检测时,将明文 PoC 变换为目标模态形式

        """
        ...

    async def get_poc_pool_cache(self, model_id: str) -> list[dict]:
        """获取指定模型的 PoC 池缓存.

        Args:
            model_id: 被测模型ID

        Returns:
            未过期的缓存条目列表,按 score 降序

        """
        ...

    async def save_poc_pool_cache(
        self,
        model_id: str,
        entries: list[dict],
        dataset_version: str,
    ) -> int:
        """批量保存 PoC 池缓存.

        Args:
            model_id: 被测模型ID
            entries: 缓存条目列表,每条包含 subtype, poc_text, score
            dataset_version: 数据集版本标识

        Returns:
            写入的条目数

        """
        ...

    async def invalidate_poc_pool_cache(self, model_id: str) -> int:
        """手动失效指定模型的 PoC 池缓存.

        Args:
            model_id: 被测模型ID

        Returns:
            删除的条目数

        """
        ...

    async def add_dataset_record(self, name: str, sample_count: int, file_path: str, risk_type: str = "", resource_id: int | None = None) -> int: ...  # noqa: D102, E501
