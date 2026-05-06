## ADDED Requirements

### Requirement: 配置可用性验证 API
系统 SHALL 提供配置可用性验证能力，通过 `schedule_config_operation` 的 `verify` 操作触发。验证时系统 SHALL 临时注册适配器、向目标大模型发送一条简短测试消息、返回验证结果后立即注销临时适配器。

#### Scenario: 验证成功
- **WHEN** 用户对 config_id=1（DeepSeek, request_format=openai, api_key 有效）调用 verify 操作
- **THEN** 系统 SHALL 返回 `{"success": true, "result": {"status": "ok", "model": "deepseek-v4-flash", "latency_ms": <int>, "response_preview": "OK"}}`

#### Scenario: 认证失败
- **WHEN** 用户对 api_key 无效的配置调用 verify 操作
- **THEN** 系统 SHALL 返回 `{"success": false, "result": {"status": "auth_failed", "error": "认证失败: Invalid API key", "latency_ms": <int>}}`

#### Scenario: 端点不可达
- **WHEN** 用户对 base_url 错误的配置调用 verify 操作
- **THEN** 系统 SHALL 返回 `{"success": false, "result": {"status": "unreachable", "error": "连接失败: ...", "latency_ms": <int>}}`

#### Scenario: 格式不匹配
- **WHEN** 用户对 request_format=anthropic 但目标 API 为 OpenAI 格式的配置调用 verify 操作
- **THEN** 系统 SHALL 返回 `{"success": false, "result": {"status": "format_mismatch", "error": "HTTP 404: ...", "latency_ms": <int>}}`

#### Scenario: 验证超时
- **WHEN** 目标大模型 30 秒内未响应
- **THEN** 系统 SHALL 返回 `{"success": false, "result": {"status": "timeout", "error": "验证超时(30s)"}}`

#### Scenario: 配置不存在
- **WHEN** 用户对不存在的 config_id 调用 verify 操作
- **THEN** 系统 SHALL 返回 `{"success": false, "error": "配置不存在"}`

#### Scenario: 验证不触发 FSM 状态转移
- **WHEN** 系统处于 idle 状态，用户调用 verify 操作
- **THEN** 系统 SHALL 保持 idle 状态不变

### Requirement: 前端配置测试按钮
PrivateConfig.vue 配置列表每行操作栏 SHALL 增加"测试"按钮。点击后 SHALL 调用 verify 操作并在弹窗中展示验证结果。

#### Scenario: 点击测试按钮-验证成功
- **WHEN** 用户点击某配置行的"测试"按钮且验证成功
- **THEN** 系统 SHALL 弹窗显示：✓ 连接成功、模型名称、响应延迟(ms)、响应预览

#### Scenario: 点击测试按钮-验证失败
- **WHEN** 用户点击某配置行的"测试"按钮且验证失败
- **THEN** 系统 SHALL 弹窗显示：✗ 连接失败、错误类型、错误详情

#### Scenario: 测试中加载状态
- **WHEN** 验证请求进行中
- **THEN** "测试"按钮 SHALL 显示 loading 状态且不可重复点击

#### Scenario: 无权限配置
- **WHEN** 用户对无访问权限的配置点击"测试"按钮
- **THEN** 系统 SHALL 提示"无访问权限"
