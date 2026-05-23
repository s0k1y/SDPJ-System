"""StateScheduler 接口定义

被依赖模块: CLI, WebUI
"""

from typing import Callable, Optional, Protocol


class StateSchedulerInterface(Protocol):
    """系统状态管理及调度控制接口

    覆盖职责 1-18：检测调度(1-4)、报告管理(5-10)、
    系统状态与日志(11-12)、用户账号(13-14)、
    权限授权(15-16)、私有资源(17-18)。
    """

    # ── 检测调度 (职责 1-4) ──

    async def start_detection(self, user_id: int, config_data: dict) -> dict:
        """接收并解析检测启动指令并下发为可执行任务组"""
        ...

    async def execute_detection_task(self, task_id: str, task_params: dict) -> dict:
        """调度执行单个检测子任务"""
        ...

    async def execute_concurrent_tasks(self, max_concurrency: int = 3) -> dict:
        """并发调度多个检测子任务"""
        ...

    async def query_detection_progress(self, task_id: Optional[str] = None) -> dict:
        """查询检测任务执行进度"""
        ...

    async def cancel_task(self, task_id: str) -> dict:
        """取消单个检测任务"""
        ...

    async def cancel_task_group(self, task_group_id: str) -> dict:
        """取消整个任务组及其关联报告"""
        ...

    # ── 报告管理调度 (职责 5-8) ──

    async def generate_report(
        self, task_group_id: str, detection_type: str, *, user_id: int | None = None
    ) -> dict:
        """生成检测报告

        Args:
            task_group_id: 任务组 ID
            detection_type: 检测类型
            user_id: 请求者用户 ID，用于权限校验
        """
        ...

    async def view_report(self, task_group_id: str, *, user_id: int | None = None) -> dict:
        """查看单份检测报告

        Args:
            task_group_id: 任务组 ID
            user_id: 请求者用户 ID，用于权限校验
        """
        ...

    async def list_reports(self, filters: Optional[dict] = None) -> list:
        """查询检测报告列表"""
        ...

    async def delete_report(
        self, target_id: str, caller_user_id: int, granularity: str = "task_group"
    ) -> dict:
        """删除检测报告"""
        ...

    async def export_report(
        self, task_group_id: str, target_format: str, *, user_id: int | None = None
    ) -> dict:
        """导出检测报告文件

        Args:
            task_group_id: 任务组 ID
            target_format: 目标文件格式
            user_id: 请求者用户 ID，用于权限校验
        """
        ...

    async def prepare_visualization_data(
        self, task_group_id: str, *, user_id: int | None = None
    ) -> dict:
        """准备可视化图表数据

        Args:
            task_group_id: 任务组 ID
            user_id: 请求者用户 ID，用于权限校验
        """
        ...

    async def prepare_task_visualization_data(
        self, task_id: str, *, user_id: int | None = None
    ) -> dict:
        """准备单个任务的可视化图表数据

        Args:
            task_id: 任务 ID
            user_id: 请求者用户 ID，用于权限校验
        """
        ...

    async def query_compliance_statistics(self) -> dict:
        """查询全局合规统计（样本级）"""
        ...

    # ── 系统状态与日志 (职责 9-12) ──

    async def startup(self) -> None:
        """应用启动时初始化（注册已入库大模型等）"""
        ...

    async def shutdown(self) -> None:
        """应用关闭时清理资源"""
        ...

    def start_task_consumer(self, interval: float = 2.0, max_concurrency: int = 3) -> None:
        """启动后台任务消费者协程"""
        ...

    async def stop_task_consumer(self) -> None:
        """停止后台任务消费者协程"""
        ...

    def get_system_state(self) -> str:
        """获取当前系统状态"""
        ...

    def subscribe_state_changes(self, callback: Callable[[str], None]) -> None:
        """订阅系统状态变更推送，callback 接收新状态字符串"""
        ...

    def unsubscribe_state_changes(self, callback: Callable[[str], None]) -> None:
        """取消订阅"""
        ...

    def subscribe_errors(self, callback: Callable[[str, str], None]) -> None:
        """订阅异常推送，callback 接收 (err_type, description)"""
        ...

    def unsubscribe_errors(self, callback: Callable[[str, str], None]) -> None:
        """取消异常订阅"""
        ...

    def subscribe_logs(self, callback: Callable[[dict], None]) -> None:
        """订阅日志推送，callback 接收日志字典"""
        ...

    def unsubscribe_logs(self, callback: Callable[[dict], None]) -> None:
        """取消日志订阅"""
        ...

    def subscribe_llm_calls(self, callback: Callable[[dict, dict], None]) -> None:
        """订阅 LLM 调用事件，callback 接收 (request_info, response_info)"""
        ...

    def unsubscribe_llm_calls(self, callback: Callable[[dict, dict], None]) -> None:
        """取消 LLM 调用订阅"""
        ...

    async def query_logs(self, filters: Optional[dict] = None) -> dict:
        """查询系统日志，返回 {"logs": [...], "total": int}"""
        ...

    # ── 用户账号调度 (职责 13-14) ──

    async def schedule_user_auth(self, username: str, password: str, action: str) -> dict:
        """调度用户注册与登录"""
        ...

    async def schedule_account_operation(self, operation: str, params: dict) -> dict:
        """调度账号管理操作（密码修改/账号切换/登出/注销/查询资料/列出资源）"""
        ...

    # ── 权限授权调度 (职责 15-16) ──

    async def schedule_dac_operation(self, operation: str, params: dict) -> dict:
        """调度自主访问控制相关操作（授予/移除/查询授权清单）"""
        ...

    async def check_resource_access(self, resource_id: int, user_id: int) -> bool:
        """在使用私有资源前的访问权前置校验"""
        ...

    # ── 私有资源调度 (职责 17, 17-1, 18) ──

    async def schedule_config_operation(self, operation: str, params: dict) -> dict:
        """调度用户私有检测配置的全生命周期管理

        支持的操作:
        - create: 创建配置 (params: config_content)
        - read: 读取配置 (params: config_id)
        - update: 更新配置 (params: config_id, config_content)
        - delete: 删除配置 (params: config_id)
        - list: 列出配置 (params: user_id)
        - export: 导出配置 (params: config_id, format)
        - import: 导入配置 (params: file_content)
        - verify: 验证配置可用性 (params: config_id)
          返回 {"success": bool, "result": { "status": "ok"|"auth_failed"|...  }}
        """
        ...

    async def query_available_datasets(self, user_id: int) -> list:
        """查询可用检测数据集清单"""
        ...

    async def query_dataset_detail(
        self, dataset_id: int, user_id: int | None = None
    ) -> dict | None:
        """查询数据集详情"""
        ...

    async def export_dataset_file(self, dataset_id: int, user_id: int | None = None) -> dict | None:
        """导出数据集文件"""
        ...

    async def import_dataset_file(self, user_id: int, filename: str, content: bytes) -> dict:
        """导入用户数据集文件"""
        ...

    async def delete_user_dataset(self, dataset_id: int, user_id: int) -> dict:
        """删除用户数据集（仅允许删除 user_datasets 下的数据集）"""
        ...

    async def schedule_private_resource_operation(self, operation: str, params: dict) -> dict:
        """调度用户私有大模型适配器与私有数据集的上传与移除"""
        ...
