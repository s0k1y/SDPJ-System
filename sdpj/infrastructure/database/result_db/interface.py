"""ResultDB 接口定义.

检测结果数据库模块的 Protocol 接口,定义所有对外暴露的能力.
DataProcessor 是唯一调用方.
"""

from datetime import datetime
from typing import Protocol


class ResultDBInterface(Protocol):
    """ResultDB 接口协议.

    定义检测结果数据库模块的所有能力,包括:
    - 检测任务组管理
    - 检测任务管理
    - 被测大模型管理
    - 检测报告管理
    - 检测结果数据管理
    """

    # ==================== 被测大模型级能力 ====================

    async def register_target_model(self, model_id: str) -> dict:
        """登记被测大模型(幂等).

        Args:
            model_id: 模型ID

        Returns:
            {"model_id": model_id}

        """
        ...

    async def get_target_model(self, model_id: str) -> dict | None:
        """查询被测大模型.

        Returns:
            {"model_id": model_id} 或 None

        """
        ...

    async def list_target_models(self) -> list[dict]:
        """列出所有被测大模型."""
        ...

    # ==================== 检测任务组级能力 ====================

    async def create_task_group(self, user_id: int, model_id: str) -> str:
        """创建检测任务组.

        Args:
            user_id: 用户ID(跨库外键,调用方需保证合法性)
            model_id: 模型ID

        Returns:
            新创建任务组的任务组ID

        Raises:
            ValueError: 模型ID在被测大模型表中不存在

        """
        ...

    async def create_task_group_with_id(self, task_group_id: str, user_id: int, model_id: str) -> str:  # noqa: E501
        """使用指定ID创建检测任务组.

        Args:
            task_group_id: 预生成的任务组ID
            user_id: 用户ID
            model_id: 模型ID

        Returns:
            任务组ID

        """
        ...

    async def delete_task_group(self, task_group_id: str) -> bool:
        """删除检测任务组.

        级联删除该任务组下的所有检测任务,检测报告与检测结果数据.

        Args:
            task_group_id: 任务组ID

        Returns:
            删除是否成功

        """
        ...

    async def list_task_groups(
        self, user_id: int | None = None, model_id: str | None = None,
    ) -> list[dict]:
        """查询检测任务组列表.

        Args:
            user_id: 用户ID过滤条件(可选)
            model_id: 模型ID过滤条件(可选)

        Returns:
            任务组元信息列表,每项包含:
            - task_group_id: 任务组ID
            - user_id: 用户ID
            - model_id: 模型ID

        """
        ...

    async def get_task_group(self, task_group_id: str) -> dict:
        """按ID查询单个检测任务组.

        Args:
            task_group_id: 任务组ID

        Returns:
            任务组元信息

        Raises:
            ValueError: 任务组不存在

        """
        ...

    # ==================== 检测任务级能力 ====================

    async def create_detection_task(
        self, task_group_id: str, dataset_id: int, task_status: str, start_time: datetime,
        *, algorithm_type: str = "static", metadata_json: dict | None = None,
    ) -> str:
        """创建检测任务.

        Args:
            task_group_id: 所属任务组ID
            dataset_id: 数据集ID(跨库外键,调用方需保证合法性)
            task_status: 初始任务状态
            start_time: 开始时间
            metadata_json: 任务元信息(可选)

        Returns:
            新创建任务的任务ID

        Raises:
            ValueError: 任务组ID不存在

        """
        ...

    async def update_task_status(
        self, task_id: str, task_status: str, end_time: datetime | None = None,
    ) -> bool:
        """更新检测任务状态.

        Args:
            task_id: 任务ID
            task_status: 任务状态
            end_time: 结束时间(可选)

        Returns:
            更新是否成功

        """
        ...

    async def mark_stale_tasks_failed(self) -> int:
        """将数据库中处于 running/pending 状态但实际已中断的任务标记为 failed.

        判定规则:
        1. task_status 为 running 且存在 report 但无 result_data → 标记 failed
        2. task_status 为 running 且无 report 且无 result_data → 标记 failed
        3. task_status 为 pending 且存在 report → 异常状态(不应有 report),标记 failed

        Returns:
            被标记为 failed 的任务数量

        """
        ...

    async def delete_detection_task(self, task_id: str) -> bool:
        """删除检测任务.

        级联删除该任务对应的检测报告与检测结果数据.

        Args:
            task_id: 任务ID

        Returns:
            删除是否成功

        """
        ...

    async def list_tasks_by_group(self, task_group_id: str) -> list[dict]:
        """按任务组ID查询任务列表.

        Args:
            task_group_id: 任务组ID

        Returns:
            该任务组下全部检测任务,每项包含:
            - task_id: 任务ID
            - dataset_id: 数据集ID
            - task_status: 任务状态
            - start_time: 开始时间
            - end_time: 结束时间

        """
        ...

    async def get_detection_task(self, task_id: str) -> dict:
        """按ID查询单个检测任务.

        Args:
            task_id: 任务ID

        Returns:
            任务详情

        Raises:
            ValueError: 任务不存在

        """
        ...

    # ==================== 检测报告级能力 ====================

    async def create_detection_report(self, task_id: str) -> str:
        """创建检测报告.

        Args:
            task_id: 所属任务ID

        Returns:
            新创建报告的检测报告ID

        Raises:
            ValueError: 任务ID不存在

        """
        ...

    async def delete_detection_report(self, report_id: str) -> bool:
        """删除检测报告.

        级联删除该报告下的全部检测结果数据.

        Args:
            report_id: 检测报告ID

        Returns:
            删除是否成功

        """
        ...

    async def list_reports_by_task_group(self, task_group_id: str) -> list[dict]:
        """按任务组ID批量查询报告(单次 JOIN 查询).

        Args:
            task_group_id: 任务组ID

        Returns:
            该任务组下所有报告列表

        """
        ...

    async def list_result_data_by_reports(self, report_ids: list[str]) -> list[dict]:
        """按多个报告ID批量查询结果数据(单次 IN 查询).

        Args:
            report_ids: 报告ID列表

        Returns:
            匹配的所有结果数据列表

        """
        ...

    async def get_report_by_task(self, task_id: str) -> dict | None:
        """按任务ID查询检测报告.

        任务与报告为1-1关系.

        Args:
            task_id: 任务ID

        Returns:
            该任务对应的报告,不存在时返回None

        """
        ...

    async def list_detection_reports(self, task_group_id: str | None = None) -> list[dict]:
        """查询检测报告列表.

        Args:
            task_group_id: 任务组ID过滤条件(可选)

        Returns:
            报告元信息列表

        """
        ...

    async def get_detection_report(self, report_id: str) -> dict:
        """按ID查询单份检测报告.

        Args:
            report_id: 检测报告ID

        Returns:
            报告元信息

        Raises:
            ValueError: 报告不存在

        """
        ...

    # ==================== 检测结果数据级能力 ====================

    async def append_result_data(  # noqa: D417, PLR0913
        self,
        report_id: str,
        risk_subclass: str,
        poc: str,
        model_output: str,
        compliance_result: str,
        iteration_count: int | None = None,
    ) -> str:
        """追加检测结果数据条目.

        Args:
            report_id: 检测报告ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果
            iteration_count: 动态检测迭代次数(可选)

        Returns:
            新创建条目的结果数据ID

        Raises:
            ValueError: 检测报告ID不存在

        """
        ...

    async def list_result_data_by_report(self, report_id: str) -> list[dict]:
        """按报告ID查询检测结果数据.

        Args:
            report_id: 检测报告ID

        Returns:
            该报告下全部结果数据明细

        """
        ...

    async def get_result_data(self, result_data_id: str) -> dict | None:
        """按ID查询单条检测结果数据.

        Args:
            result_data_id: 结果数据ID

        Returns:
            结果数据元信息,不存在时返回 None

        """
        ...

    async def count_compliance_results(self) -> dict[str, int]:
        """按合规判断结果统计数量.

        Returns:
            {compliance_result: count} 映射,如 {"合规": 800, "违规": 200}

        """
        ...

    async def clear_result_data_by_report(self, report_id: str) -> int:
        """清空指定报告下的所有结果数据.

        Args:
            report_id: 检测报告 ID

        Returns:
            被删除的记录数

        """
        ...

    async def delete_result_data(self, result_data_id: str) -> bool:
        """删除检测结果数据条目.

        Args:
            result_data_id: 结果数据ID

        Returns:
            删除是否成功

        """
        ...

    # ==================== PoC 池缓存 ====================

    async def get_poc_pool_cache(self, model_id: str) -> list[dict]:
        """获取指定模型的 PoC 池缓存(仅返回未过期条目).

        Args:
            model_id: 被测模型ID

        Returns:
            缓存条目列表,按 score 降序排列,每条包含:
            - cache_id, model_id, subtype, poc_text, score, dataset_version, created_at

        """
        ...

    async def save_poc_pool_cache(
        self,
        model_id: str,
        entries: list[dict],
        dataset_version: str,
    ) -> int:
        """批量保存 PoC 池缓存(先清除该模型旧缓存再写入).

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

    async def append_result_data_batch(
        self,
        report_id: str,
        entries: list[dict],
    ) -> list[str]:
        """批量追加检测结果数据条目.

        Args:
            report_id: 检测报告ID
            entries: 结果数据列表,每条包含:
                - risk_subclass: 风险具体子类
                - poc: 原始PoC
                - model_output: 被测大模型输出内容
                - compliance_result: 合规判断结果
                - iteration_count: 动态检测迭代次数(可选)

        Returns:
            所有新创建条目的结果数据ID列表

        Raises:
            ValueError: 检测报告ID不存在

        """
        ...

    # ==================== 报告列表摘要(高性能) ====================

    async def compute_reports_summary(
        self,
        user_id: int | None = None,
        model_id: str | None = None,
    ) -> list[dict]:
        """用 SQL 聚合查询计算报告列表摘要.

        避免对每个任务组单独查询并加载全部 result_data 大文本字段,
        仅通过 2 条 SQL 聚合查询获取列表视图所需的统计数据.

        Args:
            user_id: 用户ID过滤条件(可选)
            model_id: 模型ID过滤条件(可选)

        Returns:
            任务组列表,每组包含:
            - task_group_id: 任务组ID
            - user_id: 用户ID
            - model_id: 模型ID
            - compliance_rate: 合规率
            - risk_level: 风险等级
            - subtype_compliance: 子类型合规统计
            - status: 状态
            - children: 子任务摘要列表

        """
        ...
