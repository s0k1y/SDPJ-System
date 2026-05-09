"""UserDB 用户信息数据库模块

提供用户账号管理、资源管理、访问控制列表和私有检测配置的数据库能力。
"""

from .interface import UserDBInterface
from .models import AccessControl, PrivateConfig, Resource, User
from .session import UserDBSessionManager
from .user_db import UserDB

__all__ = [
    "UserDBInterface",
    "UserDB",
    "UserDBSessionManager",
    "User",
    "Resource",
    "AccessControl",
    "PrivateConfig",
]
