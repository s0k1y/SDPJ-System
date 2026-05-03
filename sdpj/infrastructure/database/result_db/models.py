"""ResultDB ORM 模型

使用 SQLAlchemy 2.0 异步 API 定义检测结果数据库的所有表模型。
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


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
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="用户ID（跨库引用）")
    model_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型ID（引用 TargetModel.model_id）")

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
    dataset_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="数据集ID（跨库外键）")
    task_status: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务状态")
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")

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
    model_output: Mapped[str] = mapped_column(Text, nullable=False, comment="被测大模型输出内容")
    compliance_result: Mapped[str] = mapped_column(String(50), nullable=False, comment="合规判断结果")

    # 关系
    detection_report: Mapped["DetectionReport"] = relationship(back_populates="result_data")

    def __repr__(self) -> str:
        return f"<ResultData(result_data_id={self.result_data_id}, risk_subclass={self.risk_subclass})>"
