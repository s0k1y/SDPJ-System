UtilsLib / 杂项组件库模块
具体职责:1.维护接口为上层模块提供支持
依赖模块:无
应实现接口:UtilsInterface
被依赖模块:DataProcessor,LLMInterface,LLMRegistry,UserCenter
技术细节:(暂定)
核心功能是调用提示词注入攻击检测样本数据库中的数据，通过文件处理进一步得到多模态注入数据实现多模态注入或通过编码处理进一步得到多编码数据实现多编码注入。