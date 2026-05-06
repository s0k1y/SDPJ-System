"""
SecureCommManager 接口定义

该模块定义了安全通信管理的接口契约。
"""
from __future__ import annotations

from typing import Protocol


class SecureCommManagerInterface(Protocol):
    """安全通信管理接口，被 StateScheduler 调用。"""
    ...
