## MODIFIED Requirements

### Requirement: 检测算法的并发控制参数
检测算法的并发控制 SHALL 通过函数参数 `max_rps`（float）和 `max_concurrency`（int）接收，而非硬编码模块常量。`max_rps` 默认值 SHALL 为 5.0，`max_concurrency` 默认值 SHALL 为 10。`_BATCH_SIZE` 保持模块常量 100 不变。

#### Scenario: 使用默认参数执行静态检测
- **WHEN** 调用 `run_static_detection()` 不传入 `max_rps` 和 `max_concurrency`
- **THEN** 使用默认值 `max_rps=5.0`、`max_concurrency=10`

#### Scenario: 传入自定义参数执行静态检测
- **WHEN** 调用 `run_static_detection(max_rps=1.0, max_concurrency=3)`
- **THEN** RateLimiter 使用 1.0 RPS，Semaphore 容量为 3

#### Scenario: 使用默认参数执行动态检测
- **WHEN** 调用 `run_dynamic_detection()` 不传入 `max_rps` 和 `max_concurrency`
- **THEN** 使用默认值 `max_rps=5.0`、`max_concurrency=10`
