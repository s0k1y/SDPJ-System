"""StateScheduler 接口定义"""
from typing import Protocol


class StateSchedulerInterface(Protocol):
    """系统状态管理及调度控制接口"""

    async def init(self) -> None:
        """初始化所有模块"""
        ...

    async def start_detection(self, user_id: int, config_data: dict) -> dict:
        """接收并解析检测启动指令并下发为可执行任务组

        Args:
            user_id: 用户ID
            config_data: 检测配置数据

        Returns:
            包含success和task_id的字典
        """
        ...

    async def register_user(self, username: str, password: str) -> dict:
        """注册新用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            包含success和message的字典
        """
        ...

    async def login_user(self, username: str, password: str) -> dict:
        """用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            包含success和session_id的字典
        """
        ...

    def get_system_state(self) -> str:
        """获取当前系统状态

        Returns:
            系统状态字符串
        """
        ...
