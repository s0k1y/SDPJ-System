"""ResultDB 实现

整合所有仓储层，实现 ResultDBInterface 接口。
"""

from typing import Optional
from datetime import datetime
from .interface import ResultDBInterface
from .session import SessionManager
from .repositories import (
    TaskGroupRepository,
    TaskRepository,
    ReportRepository,
    ResultDataRepository,
    TargetModelRepository,
)


class ResultDB:
    """检测结果数据库实现

    实现 ResultDBInterface 定义的所有能力。
    """

    def __init__(self, session_manager: SessionManager):
        """初始化 ResultDB

        Args:
            session_manager: 数据库会话管理器
        """
        self.session_manager = session_manager

    # ==================== 检测任务组级能力 ====================

    async def create_task_group(self, user_id: str, model_id: str) -> str:
        """创建检测任务组

        Args:
            user_id: 用户ID
            model_id: 模型ID

        Returns:
            新创建任务组的任务组ID

        Raises:
            ValueError: 模型ID在被测大模型表中不存在
        """
        async with self.session_manager.session() as session:
            # 检查模型是否存在
            target_model_repo = TargetModelRepository(session)
            if not await target_model_repo.exists(model_id):
                raise ValueError(f"模型ID '{model_id}' 在被测大模型表中不存在")

            # 生成任务组ID
            import uuid
            task_group_id = f"tg_{uuid.uuid4().hex[:16]}"

            # 创建任务组
            task_group_repo = TaskGroupRepository(session)
            await task_group_repo.create(task_group_id, user_id, model_id)

            return task_group_id

    async def delete_task_group(self, task_group_id: str) -> bool:
        """删除检测任务组

        Args:
            task_group_id: 任务组ID

        Returns:
            删除是否成功
        """
        async with self.session_manager.session() as session:
            task_group_repo = TaskGroupRepository(session)
            return await task_group_repo.delete(task_group_id)

    async def list_task_groups(
        self,
        user_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> list[dict]:
        """查询检测任务组列表

        Args:
            user_id: 用户ID过滤条件（可选）
            model_id: 模型ID过滤条件（可选）

        Returns:
            任务组元信息列表
        """
        async with self.session_manager.session() as session:
            task_group_repo = TaskGroupRepository(session)
            task_groups = await task_group_repo.list_all(user_id, model_id)

            return [
                {
                    "task_group_id": tg.task_group_id,
                    "user_id": tg.user_id,
                    "model_id": tg.model_id,
                }
                for tg in task_groups
            ]

    async def get_task_group(self, task_group_id: str) -> dict:
        """按ID查询单个检测任务组

        Args:
            task_group_id: 任务组ID

        Returns:
            任务组元信息

        Raises:
            ValueError: 任务组不存在
        """
        async with self.session_manager.session() as session:
            task_group_repo = TaskGroupRepository(session)
            task_group = await task_group_repo.get_by_id(task_group_id)

            if task_group is None:
                raise ValueError(f"任务组 '{task_group_id}' 不存在")

            return {
                "task_group_id": task_group.task_group_id,
                "user_id": task_group.user_id,
                "model_id": task_group.model_id,
            }

    # ==================== 检测任务级能力 ====================

    async def create_detection_task(
        self,
        task_group_id: str,
        dataset_id: str,
        task_status: str,
        start_time: datetime
    ) -> str:
        """创建检测任务

        Args:
            task_group_id: 所属任务组ID
            dataset_id: 数据集ID
            task_status: 初始任务状态
            start_time: 开始时间

        Returns:
            新创建任务的任务ID

        Raises:
            ValueError: 任务组ID不存在
        """
        async with self.session_manager.session() as session:
            # 检查任务组是否存在
            task_group_repo = TaskGroupRepository(session)
            if await task_group_repo.get_by_id(task_group_id) is None:
                raise ValueError(f"任务组ID '{task_group_id}' 不存在")

            # 生成任务ID
            import uuid
            task_id = f"task_{uuid.uuid4().hex[:16]}"

            # 创建任务
            task_repo = TaskRepository(session)
            await task_repo.create(task_id, task_group_id, dataset_id, task_status, start_time)

            return task_id

    async def update_task_status(
        self,
        task_id: str,
        task_status: str,
        end_time: Optional[datetime] = None
    ) -> bool:
        """更新检测任务状态

        Args:
            task_id: 任务ID
            task_status: 任务状态
            end_time: 结束时间（可选）

        Returns:
            更新是否成功
        """
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            return await task_repo.update_status(task_id, task_status, end_time)

    async def delete_detection_task(self, task_id: str) -> bool:
        """删除检测任务

        Args:
            task_id: 任务ID

        Returns:
            删除是否成功
        """
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            return await task_repo.delete(task_id)

    async def list_tasks_by_group(self, task_group_id: str) -> list[dict]:
        """按任务组ID查询任务列表

        Args:
            task_group_id: 任务组ID

        Returns:
            该任务组下全部检测任务
        """
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            tasks = await task_repo.list_by_group(task_group_id)

            return [
                {
                    "task_id": task.task_id,
                    "dataset_id": task.dataset_id,
                    "task_status": task.task_status,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                }
                for task in tasks
            ]

    async def get_detection_task(self, task_id: str) -> dict:
        """按ID查询单个检测任务

        Args:
            task_id: 任务ID

        Returns:
            任务详情

        Raises:
            ValueError: 任务不存在
        """
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            task = await task_repo.get_by_id(task_id)

            if task is None:
                raise ValueError(f"任务 '{task_id}' 不存在")

            return {
                "task_id": task.task_id,
                "task_group_id": task.task_group_id,
                "dataset_id": task.dataset_id,
                "task_status": task.task_status,
                "start_time": task.start_time,
                "end_time": task.end_time,
            }

    # ==================== 被测大模型级能力 ====================

    async def register_target_model(self, model_id: str) -> bool:
        """登记被测大模型

        Args:
            model_id: 模型ID

        Returns:
            登记是否成功
        """
        async with self.session_manager.session() as session:
            target_model_repo = TargetModelRepository(session)

            # 幂等操作：如果已存在则直接返回成功
            if await target_model_repo.exists(model_id):
                return True

            await target_model_repo.create(model_id)
            return True

    async def get_target_model(self, model_id: str) -> Optional[dict]:
        """按ID查询被测大模型

        Args:
            model_id: 模型ID

        Returns:
            被测大模型条目，不存在时返回None
        """
        async with self.session_manager.session() as session:
            target_model_repo = TargetModelRepository(session)
            model = await target_model_repo.get_by_id(model_id)

            if model is None:
                return None

            return {"model_id": model.model_id}

    # ==================== 检测报告级能力 ====================

    async def create_detection_report(self, task_id: str) -> str:
        """创建检测报告

        Args:
            task_id: 所属任务ID

        Returns:
            新创建报告的检测报告ID

        Raises:
            ValueError: 任务ID不存在
        """
        async with self.session_manager.session() as session:
            # 检查任务是否存在
            task_repo = TaskRepository(session)
            if await task_repo.get_by_id(task_id) is None:
                raise ValueError(f"任务ID '{task_id}' 不存在")

            # 生成报告ID
            import uuid
            report_id = f"report_{uuid.uuid4().hex[:16]}"

            # 创建报告
            report_repo = ReportRepository(session)
            await report_repo.create(report_id, task_id)

            return report_id

    async def delete_detection_report(self, report_id: str) -> bool:
        """删除检测报告

        Args:
            report_id: 检测报告ID

        Returns:
            删除是否成功
        """
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            return await report_repo.delete(report_id)

    async def get_report_by_task(self, task_id: str) -> Optional[dict]:
        """按任务ID查询检测报告

        Args:
            task_id: 任务ID

        Returns:
            该任务对应的报告，不存在时返回None
        """
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            report = await report_repo.get_by_task_id(task_id)

            if report is None:
                return None

            return {
                "report_id": report.report_id,
                "task_id": report.task_id,
            }

    async def list_detection_reports(
        self,
        task_group_id: Optional[str] = None
    ) -> list[dict]:
        """查询检测报告列表

        Args:
            task_group_id: 任务组ID过滤条件（可选）

        Returns:
            报告元信息列表
        """
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            reports = await report_repo.list_all(task_group_id)

            return [
                {
                    "report_id": report.report_id,
                    "task_id": report.task_id,
                }
                for report in reports
            ]

    async def get_detection_report(self, report_id: str) -> dict:
        """按ID查询单份检测报告

        Args:
            report_id: 检测报告ID

        Returns:
            报告元信息

        Raises:
            ValueError: 报告不存在
        """
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            report = await report_repo.get_by_id(report_id)

            if report is None:
                raise ValueError(f"报告 '{report_id}' 不存在")

            return {
                "report_id": report.report_id,
                "task_id": report.task_id,
            }

    # ==================== 检测结果数据级能力 ====================

    async def append_result_data(
        self,
        report_id: str,
        risk_subclass: str,
        model_output: str,
        compliance_result: str
    ) -> str:
        """追加检测结果数据条目

        Args:
            report_id: 检测报告ID
            risk_subclass: 风险具体子类
            model_output: 被测大模型输出内容
            compliance_result: 合规判断结果

        Returns:
            新创建条目的结果数据ID

        Raises:
            ValueError: 检测报告ID不存在
        """
        async with self.session_manager.session() as session:
            # 检查报告是否存在
            report_repo = ReportRepository(session)
            if await report_repo.get_by_id(report_id) is None:
                raise ValueError(f"检测报告ID '{report_id}' 不存在")

            # 生成结果数据ID
            import uuid
            result_data_id = f"result_{uuid.uuid4().hex[:16]}"

            # 创建结果数据
            result_data_repo = ResultDataRepository(session)
            await result_data_repo.create(
                result_data_id,
                report_id,
                risk_subclass,
                model_output,
                compliance_result
            )

            return result_data_id

    async def list_result_data_by_report(self, report_id: str) -> list[dict]:
        """按报告ID查询检测结果数据

        Args:
            report_id: 检测报告ID

        Returns:
            该报告下全部结果数据明细
        """
        async with self.session_manager.session() as session:
            result_data_repo = ResultDataRepository(session)
            result_data_list = await result_data_repo.list_by_report(report_id)

            return [
                {
                    "result_data_id": rd.result_data_id,
                    "report_id": rd.report_id,
                    "risk_subclass": rd.risk_subclass,
                    "model_output": rd.model_output,
                    "compliance_result": rd.compliance_result,
                }
                for rd in result_data_list
            ]

    async def delete_result_data(self, result_data_id: str) -> bool:
        """删除检测结果数据条目

        Args:
            result_data_id: 结果数据ID

        Returns:
            删除是否成功
        """
        async with self.session_manager.session() as session:
            result_data_repo = ResultDataRepository(session)
            return await result_data_repo.delete(result_data_id)
