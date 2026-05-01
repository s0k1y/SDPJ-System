LLMRegistry / 大模型注册中心模块
具体职责:
  1. 注册新的大模型
  2. 管理可用模型列表
  4. 更新模型配置
  5. 删除模型注册
  6. 验证模型可用性
  7. 处理上一层用户私有检测配置管理模块的命令
  8. 调用下一层大模型API适配库模块处理私有大模型API适配器的上传与移除
  9. 将大模型API适配库模块创建好的API调用服务实例进行注册和注销
  10. 维护注册表，在模型标识符(如Qwen、ChatGPT)与大模型API调用服务实例间建立映射
  11. 在系统启动时，调用大模型API适配库模块中所有的适配器注册大模型API调用服务实例
  12. 在系统关闭时，销毁所有大模型API服务实例
  13. 维护接口为上层模块提供支持
不需要的:[]
依赖模块:LLMAdapterLib,UtilsLib,调用接口:LLMAdapterInterface,UtilsInterface
应实现接口:LLMRegistryInterface
被依赖模块:PrivateConfigManager
技术细节:(暂定)
大模型注册中心与大模型API适配库采用了面向对象编程的思想进行设计。
注册表采用以模型标识符(如Qwen、ChatGPT)为键(Key)，以大模型API调用服务实例为值(Value)，在两者间建立映射。