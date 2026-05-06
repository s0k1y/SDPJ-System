"""ResultDB ORM 模型

使用 SQLAlchemy 2.0 异步 API 定义检测结果数据库的所有表模型。
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sdpj.infrastructure.database.base import Base


class TargetModel(Base):
    """被测大模型"""
    __tablename__ = "TargetModel"

    model_id: Mapped[str] = mapped_column(String(255), primary_key=True)


class TaskGroup(Base):
    """检测任务组表

    一次检测执行对应一个任务组。
    """
    __tablename__ = "TaskGroup"

    task_group_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="任务组ID")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    model_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("TargetModel.model_id", ondelete="RESTRICT"),
        nullable=False,
        comment="模型ID"
    )

    detection_tasks: Mapped[list["DetectionTask"]] = relationship(
        back_populates="task_group",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskGroup(task_group_id={self.task_group_id}, user_id={self.user_id}, model_id={self.model_id})>"


class DetectionTask(Base):
    """检测任务表

    每个数据集上的一次检测对应一个任务。
    """
    __tablename__ = "DetectionTask"

    task_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="任务ID")
    task_group_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("TaskGroup.task_group_id", ondelete="CASCADE"),
        nullable=False,
        comment="任务组ID"
    )
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Dataset.dataset_id", ondelete="CASCADE"),
        nullable=False,
        comment="数据集ID"
    )
    task_status: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务状态")
    algorithm_type: Mapped[str] = mapped_column(String(20), nullable=False, default="static", comment="算法类型")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="任务元信息")
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")

    # 关系
    task_group: Mapped["TaskGroup"] = relationship(back_populates="detection_tasks")
    detection_report: Mapped[Optional["DetectionReport"]] = relationship(
        back_populates="detection_task",
        cascade="all, delete-orphan",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<DetectionTask(task_id={self.task_id}, status={self.task_status})>"


class DetectionReport(Base):
    """检测报告表

    与检测任务为 1-1 关系。
    """
    __tablename__ = "DetectionReport"

    report_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="检测报告ID")
    task_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("DetectionTask.task_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="任务ID"
    )

    # 关系
    detection_task: Mapped["DetectionTask"] = relationship(back_populates="detection_report")
    result_data: Mapped[list["ResultData"]] = relationship(
        back_populates="detection_report",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DetectionReport(report_id={self.report_id}, task_id={self.task_id})>"


class ResultData(Base):
    """检测结果数据表

    存储每条样本的检测结果明细。
    """
    __tablename__ = "ResultData"

    result_data_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="结果数据ID")
    report_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("DetectionReport.report_id", ondelete="CASCADE"),
        nullable=False,
        comment="检测报告ID"
    )
    risk_subclass: Mapped[str] = mapped_column(String(255), nullable=False, comment="风险具体子类")
    poc: Mapped[str] = mapped_column(Text, nullable=False, server_default="", comment="原始PoC")
    model_output: Mapped[str] = mapped_column(Text, nullable=False, comment="被测大模型输出内容")
    compliance_result: Mapped[str] = mapped_column(String(50), nullable=False, comment="合规判断结果")
    iteration_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="动态检测迭代次数")

    # 关系
    detection_report: Mapped["DetectionReport"] = relationship(back_populates="result_data")

    def __repr__(self) -> str:
        return f"<ResultData(result_data_id={self.result_data_id}, risk_subclass={self.risk_subclass})>"


class PocPoolCache(Base):
    """PoC 池缓存表

    缓存 select_poc_pool 的筛选结果，避免每次检测重新遍历全量越狱数据集。
    """
    __tablename__ = "PocPoolCache"

    cache_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="缓存条目ID")
    model_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("TargetModel.model_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="被测模型ID"
    )
    subtype: Mapped[str] = mapped_column(String(255), nullable=False, comment="越狱攻击子类型")
    poc_text: Mapped[str] = mapped_column(Text, nullable=False, comment="预处理后的PoC文本")
    score: Mapped[int] = mapped_column(Integer, nullable=False, comment="PoC评分(1-5)")
    dataset_version: Mapped[str] = mapped_column(String(255), nullable=False, comment="数据集版本标识")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="创建时间")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True, comment="过期时间（已弃用）")

    def __repr__(self) -> str:
        return f"<PocPoolCache(cache_id={self.cache_id}, model_id={self.model_id}, subtype={self.subtype})>"


class SystemLog(Base):
    """系统日志表

    持久化存储系统运行日志。
    """
    __tablename__ = "SystemLog"

    log_id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="日志ID")
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="日志类别")
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="日志级别")
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, comment="时间戳")
    source_module: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="来源模块")
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True, comment="用户ID")
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, comment="事件类型")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="事件描述")
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="上下文信息")

    def __repr__(self) -> str:
        return f"<SystemLog(log_id={self.log_id}, category={self.category}, level={self.level})>"
