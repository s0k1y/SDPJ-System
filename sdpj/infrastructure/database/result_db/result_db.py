"""ResultDB 实现

整合所有仓储层，实现 ResultDBInterface 接口。
"""

import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, case, and_
from .interface import ResultDBInterface
from .session import SessionManager
from .repositories import (
    TaskGroupRepository,
    TaskRepository,
    ReportRepository,
    ResultDataRepository,
    TargetModelRepository,
    PocPoolCacheRepository,
)
from .repositories.log_repo import LogRepository
from .models import TaskGroup, DetectionTask, DetectionReport, ResultData, PocPoolCache


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

    # ==================== 被测大模型级能力 ====================

    async def register_target_model(self, model_id: str) -> dict:
        async with self.session_manager.session() as session:
            repo = TargetModelRepository(session)
            obj = await repo.register(model_id)
            return {"model_id": obj.model_id}

    async def get_target_model(self, model_id: str) -> Optional[dict]:
        async with self.session_manager.session() as session:
            repo = TargetModelRepository(session)
            obj = await repo.get_by_id(model_id)
            return {"model_id": obj.model_id} if obj else None

    async def list_target_models(self) -> list[dict]:
        async with self.session_manager.session() as session:
            repo = TargetModelRepository(session)
            return [{"model_id": m.model_id} for m in await repo.list_all()]

    # ==================== 检测任务组级能力 ====================

    async def create_task_group(self, user_id: int, model_id: str) -> str:
        async with self.session_manager.session() as session:
            await TargetModelRepository(session).register(model_id)
            task_group = await TaskGroupRepository(session).create(user_id, model_id)
            return task_group.task_group_id

    async def create_task_group_with_id(self, task_group_id: str, user_id: int, model_id: str) -> str:
        async with self.session_manager.session() as session:
            await TargetModelRepository(session).register(model_id)
            task_group = await TaskGroupRepository(session).create_with_id(task_group_id, user_id, model_id)
            return task_group.task_group_id

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
        user_id: Optional[int] = None,
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
        dataset_id: int,
        task_status: str,
        start_time: datetime,
        algorithm_type: str = "static",
        metadata_json: Optional[dict] = None,
        task_id: Optional[str] = None,
    ) -> str:
        async with self.session_manager.session() as session:
            task_group_repo = TaskGroupRepository(session)
            if await task_group_repo.get_by_id(task_group_id) is None:
                raise ValueError(f"任务组ID '{task_group_id}' 不存在")

            if task_id is None:
                import uuid
                task_id = f"task_{uuid.uuid4().hex[:16]}"

            task_repo = TaskRepository(session)
            await task_repo.create(
                task_id, task_group_id, dataset_id, task_status,
                start_time, algorithm_type, metadata_json
            )

            return task_id

    async def update_task_status(
        self,
        task_id: str,
        task_status: str,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新检测任务状态

        Args:
            task_id: 任务ID
            task_status: 任务状态
            end_time: 结束时间（可选）
            error_message: 错误信息（可选）

        Returns:
            更新是否成功
        """
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            return await task_repo.update_status(task_id, task_status, end_time, error_message)

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

    async def list_non_terminal_tasks(self) -> list[dict]:
        async with self.session_manager.session() as session:
            task_repo = TaskRepository(session)
            tasks = await task_repo.list_non_terminal()

            result = []
            for task in tasks:
                task_group_repo = TaskGroupRepository(session)
                tg = await task_group_repo.get_by_id(task.task_group_id)
                result.append({
                    "task_id": task.task_id,
                    "task_group_id": task.task_group_id,
                    "dataset_id": task.dataset_id,
                    "task_status": task.task_status,
                    "algorithm_type": task.algorithm_type,
                    "metadata_json": task.metadata_json,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "user_id": tg.user_id if tg else None,
                    "model_id": tg.model_id if tg else None,
                })
            return result

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

    async def list_reports_by_task_group(self, task_group_id: str) -> list[dict]:
        """按任务组ID批量查询报告（单次 JOIN 查询，替代 N+1）

        Args:
            task_group_id: 任务组ID

        Returns:
            该任务组下所有报告列表
        """
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            reports = await report_repo.list_by_task_group_id(task_group_id)
            return [
                {
                    "report_id": report.report_id,
                    "task_id": report.task_id,
                }
                for report in reports
            ]

    async def list_result_data_by_reports(self, report_ids: list[str]) -> list[dict]:
        """按多个报告ID批量查询结果数据（单次 IN 查询，替代 N+1）

        Args:
            report_ids: 报告ID列表

        Returns:
            匹配的所有结果数据列表
        """
        async with self.session_manager.session() as session:
            result_data_repo = ResultDataRepository(session)
            result_data_list = await result_data_repo.list_by_reports(report_ids)
            return [
                {
                    "result_data_id": rd.result_data_id,
                    "report_id": rd.report_id,
                    "risk_subclass": rd.risk_subclass,
                    "poc": rd.poc,
                    "model_output": rd.model_output,
                    "compliance_result": rd.compliance_result,
                    "iteration_count": rd.iteration_count,
                }
                for rd in result_data_list
            ]

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
        poc: str,
        model_output: str,
        compliance_result: str,
        iteration_count: Optional[int] = None
    ) -> str:
        """追加检测结果数据条目

        Args:
            report_id: 检测报告ID
            risk_subclass: 风险具体子类
            poc: 原始PoC
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
                poc,
                model_output,
                compliance_result,
                iteration_count
            )

            return result_data_id

    async def append_result_data_batch(
        self,
        report_id: str,
        entries: list[dict],
    ) -> list[str]:
        async with self.session_manager.session() as session:
            report_repo = ReportRepository(session)
            if await report_repo.get_by_id(report_id) is None:
                raise ValueError(f"检测报告ID '{report_id}' 不存在")

            result_ids = []
            orm_objects = []
            for entry in entries:
                result_data_id = f"result_{uuid.uuid4().hex[:16]}"
                result_ids.append(result_data_id)
                orm_objects.append(ResultData(
                    result_data_id=result_data_id,
                    report_id=report_id,
                    risk_subclass=entry["risk_subclass"],
                    poc=entry["poc"],
                    model_output=entry["model_output"],
                    compliance_result=entry["compliance_result"],
                    iteration_count=entry.get("iteration_count"),
                ))
            result_data_repo = ResultDataRepository(session)
            await result_data_repo.create_batch(orm_objects)
            return result_ids

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
                    "poc": rd.poc,
                    "model_output": rd.model_output,
                    "compliance_result": rd.compliance_result,
                    "iteration_count": rd.iteration_count,
                }
                for rd in result_data_list
            ]

    async def get_result_data(self, result_data_id: str) -> Optional[dict]:
        async with self.session_manager.session() as session:
            result_data_repo = ResultDataRepository(session)
            rd = await result_data_repo.get_by_id(result_data_id)
            if rd is None:
                return None
            return {
                "result_data_id": rd.result_data_id,
                "report_id": rd.report_id,
                "risk_subclass": rd.risk_subclass,
                "compliance_result": rd.compliance_result,
            }

    async def count_compliance_results(self) -> dict[str, int]:
        async with self.session_manager.session() as session:
            repo = ResultDataRepository(session)
            return await repo.count_by_compliance()

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

    # ==================== 系统日志级能力 ====================

    async def save_log(
        self,
        log_id: str,
        category: str,
        level: str,
        timestamp: datetime,
        source_module: str,
        user_id: Optional[str],
        event_type: str,
        description: str,
        context: Optional[dict]
    ) -> None:
        """保存系统日志

        Args:
            log_id: 日志ID
            category: 日志类别
            level: 日志级别
            timestamp: 时间戳
            source_module: 来源模块
            user_id: 用户ID
            event_type: 事件类型
            description: 事件描述
            context: 上下文信息
        """
        async with self.session_manager.session() as session:
            log_repo = LogRepository(session)
            await log_repo.create(
                log_id=log_id,
                category=category,
                level=level,
                timestamp=timestamp,
                source_module=source_module,
                user_id=user_id,
                event_type=event_type,
                description=description,
                context=context
            )

    async def query_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        source_module: Optional[str] = None,
        user_id: Optional[str] = None,
        user_ids: Optional[list[str]] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> list[dict]:
        """查询系统日志

        Args:
            category: 日志类别
            level: 日志级别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID
            user_ids: 用户ID列表（IN查询）
            limit: 返回结果数量限制
            offset: 偏移量

        Returns:
            日志列表
        """
        async with self.session_manager.session() as session:
            log_repo = LogRepository(session)
            logs = await log_repo.query(
                category=category,
                level=level,
                time_start=time_start,
                time_end=time_end,
                source_module=source_module,
                user_id=user_id,
                user_ids=user_ids,
                limit=limit,
                offset=offset
            )

            return [
                {
                    "log_id": log.log_id,
                    "category": log.category,
                    "level": log.level,
                    "timestamp": log.timestamp,
                    "source_module": log.source_module,
                    "user_id": log.user_id,
                    "event_type": log.event_type,
                    "description": log.description,
                    "context": log.context,
                }
                for log in logs
            ]

    async def count_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        source_module: Optional[str] = None,
        user_id: Optional[str] = None,
        user_ids: Optional[list[str]] = None
    ) -> int:
        """统计系统日志数量

        Args:
            category: 日志类别
            level: 日志级别
            time_start: 时间范围起始
            time_end: 时间范围结束
            source_module: 来源模块
            user_id: 用户ID
            user_ids: 用户ID列表（IN查询）

        Returns:
            匹配条件的日志数量
        """
        async with self.session_manager.session() as session:
            log_repo = LogRepository(session)
            return await log_repo.count(
                category=category,
                level=level,
                time_start=time_start,
                time_end=time_end,
                source_module=source_module,
                user_id=user_id,
                user_ids=user_ids
            )

    async def delete_old_logs(self, before: datetime) -> int:
        """删除指定时间之前的日志

        Args:
            before: 删除此时间之前的日志

        Returns:
            删除的日志数量
        """
        async with self.session_manager.session() as session:
            log_repo = LogRepository(session)
            return await log_repo.delete_old_logs(before)

    # ==================== PoC 池缓存 ====================

    async def get_poc_pool_cache(self, model_id: str) -> list[dict]:
        async with self.session_manager.session() as session:
            repo = PocPoolCacheRepository(session)
            entries = await repo.get_by_model_id(model_id)
            return [
                {
                    "cache_id": e.cache_id,
                    "model_id": e.model_id,
                    "subtype": e.subtype,
                    "poc_text": e.poc_text,
                    "score": e.score,
                    "dataset_version": e.dataset_version,
                    "created_at": e.created_at.isoformat(),
                    "expires_at": e.expires_at.isoformat() if e.expires_at else None,
                }
                for e in entries
            ]

    async def save_poc_pool_cache(
        self,
        model_id: str,
        entries: list[dict],
        dataset_version: str,
    ) -> int:
        now = datetime.now(timezone.utc)
        async with self.session_manager.session() as session:
            repo = PocPoolCacheRepository(session)
            await repo.delete_by_model_id(model_id)
            orm_entries = [
                PocPoolCache(
                    cache_id=f"cache_{uuid.uuid4().hex[:16]}",
                    model_id=model_id,
                    subtype=e["subtype"],
                    poc_text=e["poc_text"],
                    score=e["score"],
                    dataset_version=dataset_version,
                    created_at=now,
                )
                for e in entries
            ]
            await repo.save_batch(orm_entries)
            return len(orm_entries)

    async def invalidate_poc_pool_cache(self, model_id: str) -> int:
        async with self.session_manager.session() as session:
            repo = PocPoolCacheRepository(session)
            return await repo.delete_by_model_id(model_id)

    # ==================== 报告列表摘要（高性能） ====================

    async def compute_reports_summary(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[str] = None,
    ) -> list[dict]:
        """用 SQL 聚合查询计算报告列表摘要，避免 N+1 查询和加载大文本字段

        Returns:
            任务组列表，每组包含:
            - task_group_id, user_id, model_id
            - total, compliant, non_compliant, compliance_rate, risk_level
            - subtype_compliance: list[dict]
            - children: list[dict] (每个子任务的摘要)
        """
        async with self.session_manager.session() as session:
            tg_filters = []
            if user_id is not None:
                tg_filters.append(TaskGroup.user_id == user_id)
            if model_id is not None:
                tg_filters.append(TaskGroup.model_id == model_id)

            task_stats_stmt = (
                select(
                    TaskGroup.task_group_id,
                    TaskGroup.user_id,
                    TaskGroup.model_id,
                    DetectionTask.task_id,
                    DetectionTask.dataset_id,
                    DetectionTask.task_status,
                    DetectionTask.start_time,
                    DetectionTask.end_time,
                    DetectionReport.report_id,
                    func.count(ResultData.result_data_id).label("total"),
                    func.sum(
                        case(
                            (ResultData.compliance_result.startswith("合规"), 1),
                            else_=0,
                        )
                    ).label("compliant"),
                )
                .select_from(TaskGroup)
                .join(DetectionTask, TaskGroup.task_group_id == DetectionTask.task_group_id)
                .outerjoin(DetectionReport, DetectionTask.task_id == DetectionReport.task_id)
                .outerjoin(ResultData, DetectionReport.report_id == ResultData.report_id)
            )
            if tg_filters:
                task_stats_stmt = task_stats_stmt.where(and_(*tg_filters))
            task_stats_stmt = task_stats_stmt.group_by(
                TaskGroup.task_group_id,
                DetectionTask.task_id,
                DetectionReport.report_id,
            )
            task_rows = (await session.execute(task_stats_stmt)).all()

            report_ids = [row.report_id for row in task_rows if row.report_id]
            subtype_map: dict[str, list[dict]] = {}
            if report_ids:
                subtype_stmt = (
                    select(
                        DetectionReport.report_id,
                        ResultData.risk_subclass,
                        func.count().label("total"),
                        func.sum(
                            case(
                                (ResultData.compliance_result.startswith("合规"), 1),
                                else_=0,
                            )
                        ).label("passed"),
                    )
                    .select_from(ResultData)
                    .join(DetectionReport, ResultData.report_id == DetectionReport.report_id)
                    .where(DetectionReport.report_id.in_(report_ids))
                    .group_by(DetectionReport.report_id, ResultData.risk_subclass)
                )
                subtype_rows = (await session.execute(subtype_stmt)).all()
                for sr in subtype_rows:
                    subtype_map.setdefault(sr.report_id, []).append({
                        "category": sr.risk_subclass,
                        "total": sr.total,
                        "passed": int(sr.passed or 0),
                        "failed": sr.total - int(sr.passed or 0),
                        "rate": round(int(sr.passed or 0) / sr.total * 100, 2) if sr.total else 0.0,
                    })

            def _stats(total, compliant):
                if not total:
                    return {
                        "compliance_rate": 0.0,
                        "risk_level": "N/A",
                    }
                rate = compliant / total
                return {
                    "compliance_rate": round(rate * 100, 2),
                    "risk_level": "低风险" if rate >= 0.9 else ("中风险" if rate >= 0.7 else "高风险"),
                }

            groups_map: dict[str, dict] = {}
            for row in task_rows:
                tg_id = row.task_group_id
                if tg_id not in groups_map:
                    groups_map[tg_id] = {
                        "task_group_id": tg_id,
                        "user_id": row.user_id,
                        "model_id": row.model_id,
                        "_all_total": 0,
                        "_all_compliant": 0,
                        "_all_subtypes": {},
                        "children": [],
                    }
                g = groups_map[tg_id]

                task_total = row.total or 0
                task_compliant = int(row.compliant or 0)
                g["_all_total"] += task_total
                g["_all_compliant"] += task_compliant

                task_status = row.task_status or ""
                if task_status == "failed":
                    status = "failed"
                elif task_status in ("pending", "running"):
                    status = "generating"
                elif task_total > 0:
                    status = "completed"
                else:
                    status = None

                task_subtypes = subtype_map.get(row.report_id, []) if row.report_id else []
                task_stats = _stats(task_total, task_compliant)
                task_stats["subtype_compliance"] = task_subtypes

                for st in task_subtypes:
                    cat = st["category"]
                    if cat not in g["_all_subtypes"]:
                        g["_all_subtypes"][cat] = {"total": 0, "passed": 0}
                    g["_all_subtypes"][cat]["total"] += st["total"]
                    g["_all_subtypes"][cat]["passed"] += st["passed"]

                g["children"].append({
                    "task_id": row.task_id,
                    "dataset_id": row.dataset_id,
                    "report_id": row.report_id,
                    "compliance_rate": task_stats["compliance_rate"],
                    "risk_level": task_stats["risk_level"],
                    "subtype_compliance": task_subtypes,
                    "status": status,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                })

            result = []
            for g in groups_map.values():
                group_stats = _stats(g["_all_total"], g["_all_compliant"])
                group_subtypes = []
                for cat, st in g["_all_subtypes"].items():
                    failed = st["total"] - st["passed"]
                    group_subtypes.append({
                        "category": cat,
                        "total": st["total"],
                        "passed": st["passed"],
                        "failed": failed,
                        "rate": round(st["passed"] / st["total"] * 100, 2) if st["total"] else 0.0,
                    })

                has_running = any(c["status"] == "generating" for c in g["children"])
                has_failed = any(c["status"] == "failed" for c in g["children"])
                if has_running:
                    group_status = "generating"
                elif has_failed:
                    group_status = "failed"
                elif g["_all_total"] > 0:
                    group_status = "completed"
                else:
                    group_status = None

                result.append({
                    "task_group_id": g["task_group_id"],
                    "user_id": g["user_id"],
                    "model_id": g["model_id"],
                    "compliance_rate": group_stats["compliance_rate"],
                    "risk_level": group_stats["risk_level"],
                    "subtype_compliance": group_subtypes,
                    "status": group_status,
                    "children": g["children"],
                })

            return result
