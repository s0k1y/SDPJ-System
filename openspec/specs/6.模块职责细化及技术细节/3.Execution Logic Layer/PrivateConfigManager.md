PrivateConfigManager / 用户私有检测配置管理模块
具体职责:
  1. 管理用户私有检测配置（增删改查）
  2. 存储配置到加密存储
  3. 支持配置导入导出
  4. 维护接口为上层模块提供支持
不需要的:[]
依赖模块:DataProcessor,UserCenter,LLMRegistry,调用接口:DataProcessorInterface,UserCenterInterface,LLMRegistryInterface
应实现接口:PrivateConfigManagerInterface
被依赖模块:StateScheduler
技术细节:(暂定)
