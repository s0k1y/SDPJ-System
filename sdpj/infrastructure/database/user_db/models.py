"""UserDB ORM 模型定义

基于 SQLAlchemy 2.0 异步 API 的数据库模型。
符合数据库规范性 3NF 标准。
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sdpj.infrastructure.database.base import Base


class User(Base):
    """用户表

    用户(用户ID[主键], 账号, 密码)
    """
    __tablename__ = "User"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系：用户拥有的资源
    owned_resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username='{self.username}')>"


class Resource(Base):
    """资源表

    资源(资源ID[主键], 资源类型, 资源拥有者用户ID[外键_用户(用户ID)])
    """
    __tablename__ = "Resource"

    resource_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系：资源拥有者
    owner: Mapped["User"] = relationship("User", back_populates="owned_resources")

    # 关系：资源的访问控制项
    access_controls: Mapped[list["AccessControl"]] = relationship(
        "AccessControl",
        back_populates="resource",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # 关系：私有检测配置内容（一对一）
    private_config: Mapped[Optional["PrivateConfig"]] = relationship(
        "PrivateConfig",
        back_populates="resource",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<Resource(resource_id={self.resource_id}, type='{self.resource_type}', owner_id={self.owner_user_id})>"


class AccessControl(Base):
    """访问控制列表

    访问控制列表(访问控制项ID[主键], 资源ID[外键_资源(资源ID)], 被授权用户ID[外键_用户(用户ID)])
    """
    __tablename__ = "AccessControl"

    acl_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Resource.resource_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    grantee_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("User.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # 唯一约束：同一资源不能对同一用户重复授权
    __table_args__ = (
        UniqueConstraint("resource_id", "grantee_user_id", name="uq_resource_grantee"),
    )

    # 关系：所属资源
    resource: Mapped["Resource"] = relationship("Resource", back_populates="access_controls")

    # 关系：被授权用户
    grantee: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AccessControl(acl_id={self.acl_id}, resource_id={self.resource_id}, grantee_id={self.grantee_user_id})>"


class PrivateConfig(Base):
    """私有检测配置内容表

    私有检测配置内容(配置ID[主键/外键_资源(资源ID)], 配置内容JSON)
    """
    __tablename__ = "PrivateConfig"

    config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Resource.resource_id", ondelete="CASCADE"),
        primary_key=True
    )
    config_content: Mapped[str] = mapped_column(Text, nullable=False)  # 存储 JSON 字符串
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # 关系：对应的资源
    resource: Mapped["Resource"] = relationship("Resource", back_populates="private_config")

    def __repr__(self) -> str:
        return f"<PrivateConfig(config_id={self.config_id})>"
