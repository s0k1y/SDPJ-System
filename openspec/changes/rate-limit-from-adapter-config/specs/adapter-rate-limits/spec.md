## ADDED Requirements

### Requirement: 适配器 JSON 配置支持速率限制建议值
适配器 JSON 配置 SHALL 支持可选字段 `max_rps`（float，建议的每秒最大请求数，默认 0.5）和 `max_concurrency`（int，建议的最大并发数，默认 3）。未声明时 SHALL 使用保守默认值。

#### Scenario: 配置中声明了速率限制字段
- **WHEN** 适配器 JSON 配置包含 `"max_rps": 5.0` 和 `"max_concurrency": 10`
- **THEN** 系统使用配置声明的值作为建议值

#### Scenario: 配置中未声明速率限制字段
- **WHEN** 适配器 JSON 配置不包含 `max_rps` 或 `max_concurrency`
- **THEN** 系统使用默认值 `max_rps=0.5`、`max_concurrency=3`

### Requirement: 适配器暴露速率限制建议值
LLMAdapter 的 `get_metadata()` SHALL 返回 `max_rps` 和 `max_concurrency` 字段。LLMAdapterLib 的 `get_adapter_info()` SHALL 透传这两个字段。

#### Scenario: 查询适配器元信息
- **WHEN** 调用 `LLMAdapterLib.get_adapter_info(model_id)`
- **THEN** 返回结果包含 `max_rps` 和 `max_concurrency` 字段

### Requirement: 建议值可被调用方覆盖
速率限制参数 SHALL 为建议值语义，调用方（如 state_scheduler）可传入不同于建议值的 `max_rps` 和 `max_concurrency`。

#### Scenario: 调用方覆盖建议值
- **WHEN** 适配器建议 `max_rps=5.0`，但调用方传入 `max_rps=2.0`
- **THEN** 检测算法使用调用方传入的 2.0

#### Scenario: 调用方未覆盖，使用建议值
- **WHEN** 适配器建议 `max_rps=5.0`，调用方未显式传入 `max_rps`
- **THEN** 检测算法使用建议值 5.0
