## Why

当前 SDPJ 检测算法运行速度过慢，核心瓶颈有三：其一，速率限制参数 `max_rps=0.5`（每2秒仅1个请求）和并发度 `_CONCURRENCY=3` 远低于主流 LLM API 的实际承受能力，导致大量时间浪费在人为限流等待上；其二，检测结果逐条写入数据库（`append_result_data`），在高并发检测场景下产生大量独立事务开销；其三，多模态样本构造（PIL图像渲染、GIF编码）和Base64编码等CPU密集型同步操作在asyncio事件循环中直接执行，阻塞了其他协程的推进。

## What Changes

- **方案1：调整速率限制和并发参数** — 将 `_CONCURRENCY` 从3提升至10，`_BATCH_SIZE` 从50提升至100，`max_rps` 默认值从0.5提升至2.0，使检测吞吐量匹配主流付费API的实际限额（60-120 RPM）
- **方案3：批量数据库操作** — 在 `DataProcessor` 和 `ResultDB` 层新增 `append_result_data_batch` 批量写入接口，静态/动态检测器将逐条写入改为批量收集后一次性写入，减少数据库事务次数
- **方案5：异步化CPU密集型操作** — 引入 `ThreadPoolExecutor` 线程池，将 `_prepare_poc` 中的多模态构造（PIL渲染、GIF编码）、Base64编码、编码转换等同步CPU操作通过 `run_in_executor` 卸载到线程池执行，避免阻塞asyncio事件循环

## Capabilities

### New Capabilities
- `async-cpu-offload`: 将CPU密集型同步操作卸载到线程池执行的通用能力，包含全局线程池管理和 `run_cpu` 异步封装函数

### Modified Capabilities
- `SDPJDetector`: 调整并发参数（`_CONCURRENCY`、`_BATCH_SIZE`、`max_rps`默认值），将 `_prepare_poc` 改为异步版本，将检测结果写入改为批量模式
- `DataProcessor`: 新增 `append_result_data_batch` 批量写入接口
- `ResultDB`: 新增 `append_result_data_batch` 批量写入的底层实现

## Impact

- **代码变更**：`static_detector.py`、`dynamic_detector.py`、`data_processor.py`、`data_processor_interface.py`、`result_db/interface.py` 及其实现类
- **API兼容性**：`append_result_data_batch` 为新增接口，不影响现有 `append_result_data` 单条接口的向后兼容性
- **运行时行为**：检测速度显著提升，LLM API调用频率增加，需确保API配额充足；线程池引入需注意线程安全
- **依赖**：无新增外部依赖，`concurrent.futures.ThreadPoolExecutor` 为Python标准库
