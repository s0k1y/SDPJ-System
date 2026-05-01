ReportManager / 检测报告管理模块
具体职责:
  1. 在检测结束后生成标准化的检测报告
  2. 存储检测报告到ResultDB
  3. 提供报告查询接口(增删改查)
  4. 生成可视化报告图表数据
  5. 维护接口为上层模块提供支持
不需要的:[]
依赖模块:DataProcessor,UserCenter,调用接口:DataProcessorInterface,UserCenterInterface
应实现接口:ReportManagerInterface
被依赖模块:StateScheduler
技术细节:

  1.检测报告中应包含结果统计:
    1.1 安全风险率(Security Risk Rate)
      计算公式: Security_Risk_Rate = 合规输出数量 / PoC测试数据总数
      基于安全风险率判断安全风险严重性等级
      - Security Risk Rate ≥ 0.9: 安全性优秀
      - 0.7 ≤ Security Risk Rate < 0.9: 中级安全风险
      - Security Risk Rate < 0.7: 高级安全风险
    1.2 还应该了解当前学术研究动态，计算其它相关指标