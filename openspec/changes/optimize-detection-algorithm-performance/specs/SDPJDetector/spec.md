## MODIFIED Requirements

### Requirement: 检测并发参数
系统 SHALL 使用以下默认并发参数执行检测算法：
- `_CONCURRENCY` SHALL 为 10（原值 3）
- `_BATCH_SIZE` SHALL 为 100（原值 50）
- `max_rps` 默认值 SHALL 为 2.0（原值 0.5）

#### Scenario: 默认并发参数生效
- **WHEN** 调用方未显式指定 max_rps 参数启动检测
- **THEN** 系统 SHALL 使用 max_rps=2.0 作为默认速率限制

#### Scenario: 调用方可覆盖并发参数
- **WHEN** 调用方显式传入 max_rps 参数
- **THEN** 系统 SHALL 使用调用方指定的值，而非默认值

### Requirement: 检测样本预处理异步化
`_prepare_poc` 函数 SHALL 提供异步版本 `_prepare_poc_async`，在检测循环中使用异步版本替代同步版本。

#### Scenario: 静态检测使用异步预处理
- **WHEN** 静态检测器的 `_check` 协程处理样本
- **THEN** SHALL 调用 `_prepare_poc_async` 而非 `_prepare_poc`

#### Scenario: 动态检测使用异步预处理
- **WHEN** 动态检测器处理样本
- **THEN** SHALL 调用 `_prepare_poc_async` 而非 `_prepare_poc`

### Requirement: 静态检测结果批量写入
静态检测器 SHALL 在每批 gather 完成后，将批量结果通过 `append_result_data_batch` 一次性写入数据库，而非逐条调用 `append_result_data`。

#### Scenario: 静态检测批量写入
- **WHEN** 一批样本（最多 _BATCH_SIZE 条）的检测全部完成
- **THEN** 系统 SHALL 收集所有结果，调用 `append_result_data_batch` 一次性写入

### Requirement: 动态检测结果批量写入
动态检测器 SHALL 在每个数据集的所有样本处理完成后，将批量结果通过 `append_result_data_batch` 一次性写入数据库。

#### Scenario: 动态检测批量写入
- **WHEN** 一个数据集的所有样本动态检测完成
- **THEN** 系统 SHALL 收集所有结果，调用 `append_result_data_batch` 一次性写入
