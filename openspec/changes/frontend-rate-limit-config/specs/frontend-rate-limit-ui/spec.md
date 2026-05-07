## ADDED Requirements

### Requirement: 适配器配置模板包含速率限制字段
PrivateConfig.vue 中所有适配器模板 SHALL 包含 `max_rps`（float，默认 0.5）和 `max_concurrency`（int，默认 3）字段。用户在创建或编辑适配器配置时 SHALL 能通过 JSON 编辑器设置这两个字段。

#### Scenario: 新建配置时模板包含速率限制字段
- **WHEN** 用户选择任一适配器模板（OpenAI/Anthropic/系统抽象规范）新建配置
- **THEN** JSON 编辑器中的模板内容包含 `max_rps: 0.5` 和 `max_concurrency: 3`

#### Scenario: 编辑已有配置时保留速率限制字段
- **WHEN** 用户编辑一个已包含 `max_rps` 和 `max_concurrency` 的适配器配置
- **THEN** JSON 编辑器中显示该配置原有的 `max_rps` 和 `max_concurrency` 值

#### Scenario: 编辑不含速率限制字段的旧配置
- **WHEN** 用户编辑一个不包含 `max_rps` 或 `max_concurrency` 的旧适配器配置
- **THEN** JSON 编辑器中显示原有内容，不自动注入默认值（保留用户原始配置）

### Requirement: 检测启动表单支持速率限制覆盖
DetectionForm.vue 步骤2 SHALL 包含可折叠的"高级设置"区域，提供 `max_rps` 和 `max_concurrency` 输入框。用户 SHALL 可选择性地覆盖适配器建议值。不填时使用适配器建议值。

#### Scenario: 展开高级设置区域
- **WHEN** 用户在检测启动表单步骤2中点击"高级设置"
- **THEN** 展开 `max_rps`（float 输入框，步长 0.1）和 `max_concurrency`（int 输入框，步长 1）输入区域

#### Scenario: 填写速率限制覆盖值
- **WHEN** 用户在高级设置中填写 `max_rps=2.0` 和 `max_concurrency=5` 后启动检测
- **THEN** 提交的 payload 包含 `max_rps: 2.0` 和 `max_concurrency: 5`

#### Scenario: 不填写速率限制覆盖值
- **WHEN** 用户不展开高级设置或展开后不填写速率限制字段
- **THEN** 提交的 payload 不包含 `max_rps` 和 `max_concurrency` 字段，后端使用适配器建议值

#### Scenario: 确认步骤显示速率限制信息
- **WHEN** 用户在步骤3确认页面查看配置汇总
- **THEN** 如果用户设置了速率限制覆盖值，汇总中显示覆盖值；否则显示"使用适配器建议值"

### Requirement: 后端请求模型支持速率限制可选字段
DetectionStartRequest SHALL 支持可选字段 `max_rps`（Optional[float]）和 `max_concurrency`（Optional[int]）。未提供时 SHALL 为 None，表示使用适配器建议值。

#### Scenario: 请求包含速率限制覆盖值
- **WHEN** 前端提交 `max_rps=2.0` 和 `max_concurrency=5`
- **THEN** 后端 `DetectionStartRequest` 正确解析这两个字段

#### Scenario: 请求不包含速率限制字段
- **WHEN** 前端提交的 payload 不含 `max_rps` 和 `max_concurrency`
- **THEN** 后端 `DetectionStartRequest` 的这两个字段为 None

### Requirement: 调度层传递用户覆盖值到检测任务
`state_scheduler.py` 的 `start_detection()` SHALL 将用户提供的 `max_rps` 和 `max_concurrency` 覆盖值传递到检测任务参数。`execute_detection_task()` SHALL 优先使用用户覆盖值，无覆盖值时使用适配器建议值。

#### Scenario: 用户提供了覆盖值
- **WHEN** `start_detection()` 收到 `max_rps=2.0` 和 `max_concurrency=5`
- **THEN** 任务参数中包含 `max_rps=2.0` 和 `max_concurrency=5`，`execute_detection_task()` 使用这些值

#### Scenario: 用户未提供覆盖值
- **WHEN** `start_detection()` 未收到 `max_rps` 和 `max_concurrency`
- **THEN** `execute_detection_task()` 查询适配器建议值并使用
