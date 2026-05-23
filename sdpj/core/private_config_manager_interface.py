"""PrivateConfigManager 接口定义

被依赖模块: StateScheduler
"""

from typing import Literal, Optional, Protocol


class PrivateConfigManagerInterface(Protocol):
    """用户私有检测配置管理接口"""

    async def create_config(
        self, user_id: int, config_content: dict
    ) -> tuple[bool, int | None, str]:
        """创建用户私有检测配置，自动注册适配器"""
        ...

    async def read_config(self, config_id: int) -> Optional[dict]:
        """读取用户私有检测配置"""
        ...

    async def update_config(self, config_id: int, config_content: dict) -> tuple[bool, str]:
        """修改用户私有检测配置"""
        ...

    async def delete_config(self, config_id: int) -> bool:
        """删除用户私有检测配置，自动注销适配器"""
        ...

    async def list_configs(self, user_id: int) -> list[dict]:
        """列出用户的私有检测配置清单"""
        ...

    async def query_datasets(self) -> list[dict]:
        """查询可用检测数据集清单"""
        ...

    async def upload_adapter(
        self, adapter_content: str, model_id: str, user_id: int
    ) -> tuple[bool, str, int | None]:
        """上传用户私有大模型适配器"""
        ...

    async def remove_adapter(self, model_id: str, resource_id: int) -> tuple[bool, str]:
        """移除用户私有大模型适配器"""
        ...

    async def upload_dataset(
        self, name: str, risk_type: str, samples: list[dict], user_id: int
    ) -> tuple[bool, dict]:
        """上传用户私有数据集"""
        ...

    async def remove_dataset(self, dataset_id: int, resource_id: int | None = None) -> bool:
        """移除用户私有数据集"""
        ...

    async def export_config(self, config_id: int, target_format: Literal["json", "yaml"]) -> str:
        """导出用户私有检测配置"""
        ...

    async def import_config(self, file_content, user_id: int) -> tuple[bool, int | None, str]:
        """导入用户私有检测配置

        Args:
            file_content: 配置内容，支持 str（原始 JSON/YAML 文本）或 dict（已解析的配置对象）
            user_id: 用户 ID

        Returns:
            (成功标志, 配置ID, 提示消息)
        """
        ...

    async def import_dataset_file(
        self, user_id: int, filename: str, content: bytes, username: str
    ) -> dict:
        """导入用户数据集文件
        Returns: {"success": bool, "dataset_id": int | None, "error": str | None}
        """
        ...

    async def export_dataset_file(
        self, dataset_id: int, username: str | None = None
    ) -> dict | None:
        """导出数据集文件
        Returns: {"content": str, "filename": str} 或 None
        """
        ...

    # LLMRegistry 委托方法（供 StateScheduler 通过本模块间接调用）
    async def initialize_registry(self) -> bool: ...
    async def shutdown_registry(self) -> bool: ...
    async def is_model_available(self, model_id: str) -> tuple[bool, any]: ...
    def get_adapter_info(self, model_id: str) -> dict: ...
    async def register_private_model(
        self, adapter_content: str, model_id: str
    ) -> tuple[bool, str, str]: ...
    async def unregister_private_model(self, model_id: str) -> tuple[bool, str]: ...
