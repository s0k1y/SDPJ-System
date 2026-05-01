DataProcessor / 检测数据处理模块
具体职责:
  1. 将执行逻辑层的具体指令解析为对应数据库查询语句，对检测样本数据库，检测结果数据库进行增删查改，并调用杂项组件库实现对检测数据进行处理，以实现特定类型风险检测的数据格式调整，如提示词注入攻击中间接注入,多编码注入,多模态注入的实现。
  2.维护接口为上层模块提供支持

不需要的:[处理检测数据的清洗和预处理,格式化检测输入数据,管理数据缓存]

依赖模块:SampleDB,ResultDB,UtilsLib,调用接口:SampleDBInterface,ResultDBInterface,UtilsInterface
应实现接口:DataProcessorInterface
被依赖模块:SDPJDetector,PrivateConfigManager,ReportManager
技术细节:

