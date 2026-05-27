"""SampleDB ORM 模型定义.

使用 SQLAlchemy 2.0 异步 ORM 定义检测样本数据库的数据模型.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdpj.infrastructure.database.base import Base


class Dataset(Base):
    """安全风险检测数据集.

    对应规格文档中的实体:安全风险检测数据集
    属性:数据集ID,数据集名称,安全风险类型
    """

    __tablename__ = "Dataset"

    # 主键
    dataset_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 数据集名称(唯一约束)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # 安全风险类型(如「越狱攻击」「提示词注入」「安全基准」)
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # 对应 UserDB Resource 表的 resource_id(内置数据集为 NULL)
    resource_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("Resource.resource_id", ondelete="SET NULL"), nullable=True, index=True,
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False,
    )

    # 关系:一个数据集包含多个检测样本
    samples: Mapped[list["DetectionSample"]] = relationship(
        "DetectionSample", back_populates="dataset", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:  # noqa: D105
        return f"<Dataset(id={self.dataset_id}, name='{self.name}', risk_type='{self.risk_type}')>"


class DetectionSample(Base):
    """检测样本数据.

    对应规格文档中的实体:检测样本数据
    属性:样本ID,风险具体子类,漏洞概念验证数据
    关系:n个检测样本数据属于1个数据集
    """

    __tablename__ = "DetectionSample"

    # 主键
    sample_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 风险具体子类 ST
    subtype: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # 漏洞概念验证数据 PoC(使用 Text 类型支持长文本)
    poc: Mapped[str] = mapped_column(Text, nullable=False)

    # 外键:所属数据集 ID
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("Dataset.dataset_id", ondelete="CASCADE"), nullable=False, index=True,
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False,
    )

    # 关系:多个样本属于一个数据集
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="samples")

    def __repr__(self) -> str:  # noqa: D105
        return f"<DetectionSample(id={self.sample_id}, subtype='{self.subtype}', dataset_id={self.dataset_id})>"  # noqa: E501


class SystemMeta(Base):
    """系统元数据.

    用于存储系统级别的键值对配置信息.
    """

    __tablename__ = "SystemMeta"

    # 主键
    meta_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 键(唯一约束)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # 值
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False,
    )

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:  # noqa: D105
        return f"<SystemMeta(id={self.meta_id}, key='{self.key}')>"
