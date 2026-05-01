StateScheduler / 系统状态管理及调度控制模块

具体职责:
  1. 作为执行逻辑层的操作系统管理系统运行状态
  2. 接收并解析用户指令
  3. 调度控制执行逻辑层各模块
  4. 处理系统异常和错误恢复
  5. 维护接口为上层模块提供支持
不需要的:[监控系统资源使用情况]

依赖模块:TaskQueueManager,EventLogger,SecureCommManager,SDPJDetector,ReportManager,PrivateConfigManager,DACManager,AccountManager
调用接口:TaskQueueManagerInterface,EventLoggerInterface,SecureCommManagerInterface,SDPJDetectorInterface,ReportManagerInterface,PrivateConfigManagerInterface,DACManagerInterface,AccountManagerInterface

被依赖模块:CLI,WebUI
应实现接口:StateSchedulerInterface

技术细节:

1.系统状态管理

  1.1状态定义
    - 通过预设定好的系统状态头文件规定系统的状态

  1.2有限状态机实现
    - 通过有限状态机（FSM）的实现来跟踪系统当前所处状态
    - 根据有限状态机状态转移条件进行对应状态的转移和对应行动的执行

  1.3状态管理行为
    - 维护系统当前所处状态及状态间的转移和行为
    - 便于系统进行异常处理
    - 向用户反馈指令执行情况
    - 使用户得以了解当前系统的运行情况和检测任务的执行进度

2.调度控制模块

  2.1指令解析与转换
    - 接收用户指令，解析用户指令中的意图
    - 将用户意图指令解析，转换为实际调用指令
    - 示例：当用户选择了多个安全风险的检测类型时，为实现这一意图，转换为"一个检测任务组"
      - 检测任务组包含对不同检测数据集的检测任务
      - 调用执行逻辑层中的检测任务队列管理模块管理检测任务(并行任务是否可以通过连续入队/出队多个来实现),并调用SDPJDetector进行具体的执行

  2.2并发执行
    - 实现多个逻辑层模块的并发执行
    - 支持多个检测任务并行处理
    - 协调并调用执行逻辑层各组件执行用户指令

  2.3执行协调
    - 与系统日志与事件管理模块交互,记录和反馈系统日志
    - 向CLI/WebUI反馈指令执行情况
    - 处理系统异常和错误恢复(依赖于有限状态机的状态转移条件)
    - 调用安全通信管理模块, 在C-S通信(webUI)中加解密敏感数据（账号密码、大模型API配置文件）,这一点应在StateSchedulerInterface中定义
    - 调用执行逻辑层其它模块



