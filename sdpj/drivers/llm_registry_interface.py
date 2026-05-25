"""
LLMRegistryInterface - 大模型注册中心接口定义

职责:
1. 启动时批量注册已入库大模型
2. 查询已注册大模型清单
3. 按标识校验大模型是否可用
4. 注册用户上传的私有大模型
5. 注销用户移除的私有大模型
6. 关闭期批量销毁全部服务实例

依赖模块: LLMAdapterLib, UtilsLib
被依赖模块: PrivateConfigManager
"""

from typing import Any, Dict, List, Optional, Protocol, Tuple


class ModelInfo:
    """已注册大模型信息"""

    def __init__(
        self,
        model_id: str,
        adapter_name: str,
        version: str,
        description: str = "",
        supported_features: List[str] | None = None,
    ):
        """
        初始化大模型信息

        Args:
            model_id: 大模型标识
            adapter_name: 适配器名称
            version: 适配器版本
            description: 描述信息
            supported_features: 支持的特性列表
        """
        self.model_id = model_id
        self.adapter_name = adapter_name
        self.version = version
        self.description = description
        self.supported_features = supported_features or []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "model_id": self.model_id,
            "adapter_name": self.adapter_name,
            "version": self.version,
            "description": self.description,
            "supported_features": self.supported_features,
        }


class LLMRegistryInterface(Protocol):
    """大模型注册中心接口"""

    async def initialize(self) -> bool:
        """
        启动时批量注册已入库大模型

        Returns:
            bool: 批量注册是否成功

        后置条件:
            所有已入库适配器对应的 API 调用服务实例已写入注册表
            (以模型标识为键、服务实例为值)

        触发场景:
            系统启动期,为后续用户选择/调用大模型提供可用视图
        """
        ...

    async def list_registered_models(self) -> List[ModelInfo]:
        """
        查询已注册大模型清单

        Returns:
            List[ModelInfo]: 已注册大模型标识列表及其元信息

        触发场景:
            用户在私有检测配置中浏览/选择可用大模型
        """
        ...

    async def is_model_available(self, model_id: str) -> Tuple[bool, Optional[Any]]:
        """
        按标识校验大模型是否可用

        Args:
            model_id: 大模型标识

        Returns:
            Tuple[bool, Optional[Any]]: (是否已注册, 服务实例句柄或None)

        触发场景:
            PrivateConfigManager 在写入/读取用户私有检测配置涉及指定大模型时做合法性校验
        """
        ...

    async def register_private_model(
        self, adapter_content: str, model_id: str
    ) -> Tuple[bool, str, str]:
        """
        注册用户上传的私有大模型

        Args:
            adapter_content: 用户上传的适配器文件内容
            model_id: 目标大模型标识

        Returns:
            Tuple[bool, str, str]: (注册是否成功, 新登记的大模型标识, 错误信息)

        后置条件:
            适配器已入库且对应服务实例已写入本模块注册表

        触发场景:
            用户上传私有大模型适配器

        错误情形:
            - 文件格式校验不通过时拒绝注册
            - 适配器不符合大模型服务接口规范
            - 同标识已存在等错误由下层透传

        不负责的边界:
            不做调用方权限判定(由 DACManager 完成)
        """
        ...

    async def unregister_private_model(self, model_id: str) -> Tuple[bool, str]:
        """
        注销用户移除的私有大模型

        Args:
            model_id: 目标大模型标识

        Returns:
            Tuple[bool, str]: (移除是否成功, 错误信息)

        后置条件:
            对应服务实例已从注册表中清除,适配器制品已从 LLMAdapterLib 库中移除

        触发场景:
            用户移除私有大模型适配器
        """
        ...

    def get_adapter_info(self, model_id: str) -> dict:
        """按大模型标识查询适配器元信息

        Args:
            model_id: 大模型标识

        Returns:
            dict: 适配器元信息（包含 max_rps, max_concurrency 等字段）
        """
        ...

    async def shutdown(self) -> bool:
        """
        关闭期批量销毁全部服务实例

        Returns:
            bool: 销毁是否成功

        后置条件:
            注册表清空;下层持有的服务实例资源全部释放

        触发场景:
            系统关闭期
        """
        ...

    async def close_adapter_sessions(self) -> None:
        """
        关闭所有已注册适配器的HTTP会话（不销毁实例）

        后置条件:
            所有 aiohttp ClientSession 已关闭，适配器实例可下次惰性重建

        触发场景:
            CLI 模式下单次检测完成后释放网络资源
        """
        ...
