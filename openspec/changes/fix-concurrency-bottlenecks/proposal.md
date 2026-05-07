## Why

当前 SDPJ 检测算法运行极慢（5.5-13.5小时，理论最优79分钟），根因有三：其一，RateLimiter 使用 asyncio.Lock 互斥锁实现速率控制，将"限速"错误实现为"串行"，导致 Semaphore(10) 形同虚设，实际并发度降为1；其二，动态检测（dynamic_detector.py）使用四层嵌套 for 循环 + await，完全无并发，约2932个合规样本逐个串行处理；其三，DataProcessor 的 load_dataset_by_risk_type 和 aggregate_task_group_results 存在 N+1 查询模式。

## What Changes

- **令牌桶 RateLimiter** — 用令牌桶算法替代当前互斥锁实现，令 acquire() 无需持有锁即可通过（桶中有令牌时立即返回），仅在令牌不足时短暂等待，实现真正的"限速而非串行"
- **动态检测并发化** — 在 dynamic_detector.py 中引入 Semaphore + asyncio.gather，将合规样本的处理从串行改为并发，与静态检测保持一致的并发架构
- **N+1 查询优化** — 在 DataProcessor.load_dataset_by_risk_type 中使用单次 JOIN 查询替代逐数据集查询样本；在 aggregate_task_group_results 中使用批量查询替代逐任务查询报告和结果

## Capabilities

### New Capabilities
- `token-bucket-rate-limiter`: 令牌桶速率控制器，替代互斥锁实现的 RateLimiter，支持真正的并发限速

### Modified Capabilities
- `SDPJDetector`: 动态检测从串行改为并发，需新增 Semaphore 和 RateLimiter 实例，合规样本处理改为 asyncio.gather 并发调度
- `DataProcessor`: load_dataset_by_risk_type 和 aggregate_task_group_results 的查询模式从 N+1 改为批量 JOIN

## Impact

- **代码变更**：`rate_limiter.py`（重写）、`dynamic_detector.py`（并发化改造）、`data_processor.py`（查询优化）、`sample_db.py`（新增批量查询方法）、`result_db.py`（新增批量查询方法）
- **API兼容性**：RateLimiter 的 `acquire()` 接口不变，仅内部实现变更，向后兼容；DataProcessor 新增内部方法，不影响对外接口
- **运行时行为**：检测吞吐量预计提升 4-10 倍，LLM API 调用频率增加，需确保 API 配额充足；令牌桶允许突发请求，但受 max_rps 参数约束
- **依赖**：无新增外部依赖，令牌桶算法为纯 Python 标准库实现
