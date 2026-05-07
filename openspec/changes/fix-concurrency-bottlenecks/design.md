## Context

SDPJ 检测系统当前运行缓慢，核心瓶颈有三个：
1. **RateLimiter 互斥锁**：`rate_limiter.py` 的 `acquire()` 使用 `asyncio.Lock` + `asyncio.sleep` 在锁内等待，将并发降为串行，Semaphore(10) 形同虚设
2. **动态检测串行**：`dynamic_detector.py` 四层嵌套 for 循环 + await，约2932个合规样本逐个串行处理
3. **N+1 查询**：`data_processor.py` 的 `load_dataset_by_risk_type` 和 `aggregate_task_group_results` 存在 N+1 查询模式

当前架构：static_detector.py / dynamic_detector.py → DataProcessor → ResultDB/SampleDB（SQLAlchemy async session），检测循环使用 asyncio.Semaphore + RateLimiter 控制并发。

## Goals / Non-Goals

**Goals:**
- 将 RateLimiter 从互斥锁实现改为令牌桶实现，使并发度从1恢复到 Semaphore 允许的10
- 将动态检测从串行改为并发，引入 Semaphore + asyncio.gather
- 消除 DataProcessor 中的 N+1 查询模式
- 将检测总耗时从5.5-13.5小时降至约79分钟（理论最优）

**Non-Goals:**
- 不改变检测算法逻辑（SDPJ Algorithm 1/2 的步骤和流程不变）
- 不改变数据库表结构（不新增表、不修改字段）
- 不改变 LLMService 的重试策略（tenacity 配置保持不变）
- 不引入自适应速率控制（根据429动态调整max_rps），留作后续优化
- 不改变 RateLimiter 的对外接口（acquire() 签名不变）

## Decisions

### 决策1：令牌桶算法替代互斥锁

**选择**：令牌桶（Token Bucket）算法

**理由**：
- 互斥锁的问题本质：`asyncio.Lock` 将"限速"（单位时间内不超过N个请求）实现为"串行"（同一时刻只有1个请求）
- 令牌桶以恒定速率向桶中添加令牌，acquire() 只需取一个令牌，无需互斥
- 桶空时才等待，桶有令牌时立即通过，多个协程可以同时 acquire()
- 锁仅保护令牌计数的读写（微秒级），不保护 sleep（在锁外等待）

**实现要点**：
- `_tokens`：当前令牌数（浮点数，支持分数令牌）
- `_max_tokens`：桶容量 = max_rps（允许短时突发）
- `_rate`：令牌添加速率 = max_rps 个/秒
- `_last_refill`：上次填充时间
- acquire() 流程：refill → 有令牌则扣减返回 → 无令牌则计算等待时间 → 在锁外 sleep → 重试

**备选方案**：滑动窗口计数器——实现更复杂，且不支持突发；漏桶——输出速率恒定，不支持突发，不适合 LLM API 场景

### 决策2：动态检测并发化策略

**选择**：与静态检测一致的 Semaphore + asyncio.gather 架构

**理由**：
- 动态检测中每个合规样本的处理完全独立（无数据依赖），天然可并行
- 复用静态检测已验证的并发架构，降低实现风险
- 使用相同的 _CONCURRENCY=10 和 RateLimiter 参数

**实现要点**：
- 在 run_dynamic_detection 中创建 Semaphore(_CONCURRENCY) 和 RateLimiter
- 将三层嵌套循环（task → result_data → poc_pool × iterations）改为：先收集所有合规样本，再用 asyncio.gather 并发处理
- 每个样本的处理函数内部仍保持 poc_pool 循环和 iteration 循环的串行（因为迭代间有数据依赖）
- 批量写入：每批 gather 完成后调用 append_result_data_batch

**备选方案**：将 poc_pool 维度也并发化——增加复杂度且收益有限（同一样本的不同 PoC 之间有逻辑关联：一个 PoC 成功即 break）

### 决策3：N+1 查询优化策略

**选择**：在 SampleDB 和 ResultDB 层新增批量查询方法

**理由**：
- load_dataset_by_risk_type：新增 get_samples_by_risk_type 方法，一次 JOIN 查询替代 N 次逐数据集查询
- aggregate_task_group_results：新增批量查询方法，一次查询获取所有任务的报告和结果数据

**实现要点**：
- SampleDB 新增 `get_samples_by_risk_type(risk_type)` 方法，使用 JOIN 查询
- ResultDB 新增 `list_reports_by_group(task_group_id)` 和 `list_result_data_by_reports(report_ids)` 方法
- DataProcessor 调用新方法替代逐条查询

## Risks / Trade-offs

- **[令牌桶突发流量]** → 桶容量 = max_rps，最多允许 max_rps 个请求同时发出 → 受 Semaphore(10) 二次约束，实际并发不超过10 → 风险可控
- **[动态检测并发后429增加]** → 并发度提升后可能更频繁触发限流 → 四层防线架构（RateLimiter + Semaphore + tenacity重试 + Retry-After头提取）已覆盖
- **[批量查询内存占用]** → 一次加载所有样本到内存 → 内置数据集最大约30000样本，每样本约200字节 → 约6MB，可接受
- **[向后兼容性]** → RateLimiter.acquire() 接口不变 → 所有调用方无需修改
