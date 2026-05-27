"""PrivateConfigManager 接口定义.

被依赖模块: StateScheduler
"""

from typing import Any, Literal, Protocol


class PrivateConfigManagerInterface(Protocol):
    """用户私有检测配置管理接口."""

    async def create_config(
        self, user_id: int, config_content: dict,
    ) -> tuple[bool, int | None, str]:
        """创建用户私有检测配置,自动注册适配器."""
        ...

    async def read_config(self, config_id: int) -> dict | None:
        """读取用户私有检测配置."""
        ...

    async def update_config(self, config_id: int, config_content: dict) -> tuple[bool, str]:
        """修改用户私有检测配置."""
        ...

    async def delete_config(self, config_id: int) -> bool:
        """删除用户私有检测配置,自动注销适配器."""
        ...

    async def list_configs(self, user_id: int) -> list[dict]:
        """列出用户的私有检测配置清单."""
        ...

    async def query_datasets(self) -> list[dict]:
        """查询可用检测数据集清单."""
        ...

    async def upload_adapter(
        self, adapter_content: str, model_id: str, user_id: int,
    ) -> tuple[bool, str, int | None]:
        """上传用户私有大模型适配器."""
        ...

    async def remove_adapter(self, model_id: str, resource_id: int) -> tuple[bool, str]:
        """移除用户私有大模型适配器."""
        ...

    async def upload_dataset(
        self, name: str, risk_type: str, samples: list[dict], user_id: int,
    ) -> tuple[bool, dict]:
        """上传用户私有数据集."""
        ...

    async def remove_dataset(self, dataset_id: int, resource_id: int | None = None) -> bool:
        """移除用户私有数据集."""
        ...

    async def export_config(self, config_id: int, target_format: Literal["json", "yaml"]) -> str:
        """导出用户私有检测配置."""
        ...

    async def import_config(self, file_content, user_id: int) -> tuple[bool, int | None, str]:  # noqa: ANN001
        """导入用户私有检测配置.

        Args:
            file_content: 配置内容,支持 str(原始 JSON/YAML 文本)或 dict(已解析的配置对象)
            user_id: 用户 ID

        Returns:
            (成功标志, 配置ID, 提示消息)

        """
        ...

    async def import_dataset_file(
        self, user_id: int, filename: str, content: bytes, username: str,
    ) -> dict:
        """导入用户数据集文件  # noqa: "dataset_id": int | None, "error": str | None}., D200, D205        Returns: {"success": bool, E501
        """
        ...

    async def export_dataset_file(
        self, dataset_id: int, username: str | None = None,
    ) -> dict | None:
        """导出数据集文件  # noqa: "filename": str} 或 None., D200, D205        Returns: {"content": str
        """
        ...

    # LLMRegistry 委托方法(供 StateScheduler 通过本模块间接调用)
    async def initialize_registry(self) -> bool: ...  # noqa: D102
    async def shutdown_registry(self) -> bool: ...  # noqa: D102
    async def is_model_available(self, model_id: str) -> tuple[bool, Any]: ...  # noqa: D102
    def get_adapter_info(self, model_id: str) -> dict: ...  # noqa: D102
    async def register_private_model(  # noqa: D102
        self, adapter_content: str, model_id: str,
    ) -> tuple[bool, str, str]: ...
    async def unregister_private_model(self, model_id: str) -> tuple[bool, str]: ...  # noqa: D102
    async def close_adapter_sessions(self) -> None: ...  # noqa: D102

    async def read_configs_batch(self, config_ids: list[int]) -> dict[int, dict]: ...  # noqa: D102
