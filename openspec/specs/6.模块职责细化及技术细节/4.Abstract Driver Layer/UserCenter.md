UserCenter / 用户管理中心模块
具体职责:
  1. 将执行逻辑层的具体指令解析为对应数据库查询语句，进一步与用户信息数据库进行交互，实现用户账号管理中，注册，登录，密码修改，账号切换四大基本操作的实际执行。
  2. 用户权限管理
  3. 维护接口为上层模块提供支持
不需要的:[用户会话管理]
依赖模块:UserDB,UtilsLib,调用接口:UserDBInterface,UtilsInterface
应实现接口:UserCenterInterface
被依赖模块:PrivateConfigManager,ReportManager,AccountManager,DACManager
技术细节:(暂定)
