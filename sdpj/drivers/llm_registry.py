"""
LLMRegistry - 大模型注册中心实现

职责:
1. 启动时批量注册已入库大模型
2. 查询已注册大模型清单
3. 按标识校验大模型是否可用
4. 注册用户上传的私有大模型
5. 注销用户移除的私有大模型
6. 关闭期批量销毁全部服务实例

依赖: LLMAdapterLib, UtilsLib
"""

from typing import Dict, List, Optional, Any


class LLMRegistry:
    """大模型注册中心"""

    def __init__(self, adapter_registry: Any = None, utils_lib: Any = None):
        """初始化LLMRegistry

        Args:
            adapter_registry: 适配器注册中心(可选)
            utils_lib: 工具库(可选)
        """
        self.adapter_registry = adapter_registry
        self.utils_lib = utils_lib
        self.adapters: Dict[str, dict] = {}
        self._registry: Dict[str, Any] = {}

    async def startup(self) -> None:
        """启动注册中心"""
        pass

    async def initialize(self) -> bool:
        """初始化并批量注册已入库大模型"""
        if self.adapter_registry:
            try:
                adapters = await self.adapter_registry.list_adapters()
                for adapter in adapters:
                    model_id = adapter.get('model_id')
                    if model_id:
                        self.adapters[model_id] = adapter
                        self._registry[model_id] = adapter
                return True
            except Exception:
                return False
        return True

    async def list_registered_models(self) -> List[Any]:
        """列出所有已注册的模型(返回ModelInfo列表)"""
        result = []
        for model_id, service in self._registry.items():
            try:
                # 尝试获取元信息
                if self.adapter_registry and hasattr(self.adapter_registry, 'get_adapter_metadata'):
                    metadata = await self.adapter_registry.get_adapter_metadata(model_id)
                    result.append(metadata)
                else:
                    # 简单返回模型ID
                    from sdpj.drivers.llm_registry_interface import ModelInfo
                    result.append(ModelInfo(model_id=model_id))
            except Exception:
                # 跳过获取元信息失败的模型
                continue
        return result

    def list_models(self) -> List[str]:
        """列出所有已注册的模型ID"""
        return list(self.adapters.keys())

    def get_model_info(self, model_id: str) -> Optional[dict]:
        """获取模型信息"""
        return self.adapters.get(model_id)

    async def is_model_available(self, model_id: str) -> tuple[bool, Any]:
        """检查模型是否可用,返回(是否可用, 服务实例)"""
        if model_id in self._registry:
            return True, self._registry[model_id]
        return False, None

    async def register_model(self, model_id: str, config: dict) -> bool:
        """注册新模型"""
        self.adapters[model_id] = config
        self._registry[model_id] = config
        return True

    async def register_private_model(self, adapter_content: str, model_id: str) -> tuple[bool, str, str]:
        """注册私有模型

        Returns:
            (成功标志, 注册的模型ID, 错误信息)
        """
        try:
            # 1. 文件格式校验
            if self.utils_lib and hasattr(self.utils_lib, 'validate_file_format'):
                is_valid, error_msg = self.utils_lib.validate_file_format(adapter_content, 'json')
                if not is_valid:
                    return False, "", f"文件格式校验失败: {error_msg}"

            # 2. 调用adapter_registry注册
            if self.adapter_registry and hasattr(self.adapter_registry, 'register_adapter'):
                service = await self.adapter_registry.register_adapter(adapter_content, model_id)
                self._registry[model_id] = service
                self.adapters[model_id] = {'model_id': model_id}
                return True, model_id, ""

            # 简单注册
            self._registry[model_id] = {'model_id': model_id}
            self.adapters[model_id] = {'model_id': model_id}
            return True, model_id, ""

        except Exception as e:
            error_type = type(e).__name__
            if 'Validation' in error_type:
                return False, "", str(e)
            elif 'AlreadyExists' in error_type:
                return False, "", str(e)
            else:
                return False, "", f"注册失败: {str(e)}"

    async def unregister_model(self, model_id: str) -> bool:
        """注销模型"""
        if model_id in self.adapters:
            del self.adapters[model_id]
            if model_id in self._registry:
                del self._registry[model_id]
            return True
        return False

    async def unregister_private_model(self, model_id: str) -> tuple[bool, str]:
        """注销私有模型

        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 检查是否存在
            if model_id not in self._registry:
                return False, f"模型 {model_id} 不存在"

            # 调用adapter_registry注销
            if self.adapter_registry and hasattr(self.adapter_registry, 'unregister_adapter'):
                success = await self.adapter_registry.unregister_adapter(model_id)
                if not success:
                    return False, f"模型 {model_id} 不存在"

            # 从注册表移除
            if model_id in self._registry:
                del self._registry[model_id]
            if model_id in self.adapters:
                del self.adapters[model_id]

            return True, ""

        except Exception as e:
            return False, f"注销失败: {str(e)}"

    async def shutdown(self) -> bool:
        """关闭并销毁所有服务实例"""
        try:
            # 销毁所有服务实例
            if self.adapter_registry and hasattr(self.adapter_registry, 'destroy_service_instance'):
                for model_id, service in list(self._registry.items()):
                    await self.adapter_registry.destroy_service_instance(service)

            # 清空注册表
            self.adapters.clear()
            self._registry.clear()
            return True
        except Exception:
            return False
