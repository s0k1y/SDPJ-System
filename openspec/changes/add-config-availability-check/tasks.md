## 1. 后端：StateScheduler 新增 verify 操作

- [x] 1.1 在 `state_scheduler.py` 的 `schedule_config_operation` 方法中新增 `verify` 操作分支：读取配置 → 临时注册适配器（UUID model_id）→ asyncio.wait_for 调用 LLM → 注销适配器 → 返回验证结果
- [x] 1.2 在 `state_scheduler_interface.py` 的接口文档中补充 verify 操作说明

## 2. 前端：PrivateConfig.vue 增加测试按钮

- [x] 2.1 在配置列表操作栏增加"测试"按钮，绑定 verifyConfig 方法
- [x] 2.2 实现 verifyConfig 方法：调用 detectionConfig('verify', { config_id })，处理加载状态
- [x] 2.3 实现验证结果弹窗展示：成功显示 ✓ 连接成功/模型/延迟/响应预览，失败显示 ✗ 错误类型/详情
