LLMInterface / 大模型服务接口模块
具体职责:
  1. 在执行检测任务时调用大模型API作为基础服务支持
  2. 管理大模型请求和响应
  3. 处理API限流和重试
  4. 统一不同大模型的接口差异
  5. 管理会话上下文
  6. 维护接口为上层模块提供支持
不需要的:[记录API调用日志]
依赖模块:LLMAdapterLib,UtilsLib,调用接口:LLMAdapterInterface,UtilsInterface
应实现接口:LLMServiceInterface
被依赖模块:SDPJDetector
技术细节:(暂定)
定义统一的大模型API调用服务接口,包括API调用的抽象方法,但不负责具体实现,执行逻辑层只通过该接口所提供的抽象方法进行逻辑实现,具体实现由基础设施层中的大模型API适配库模块进行实现，从而避免对大模型具体API调用中技术细节(如API调用方法,格式)的依赖。