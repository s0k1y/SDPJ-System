## Context

SDPJ 检测系统当前运行缓慢，核心瓶颈有三：
1. **速率限制过严**：`max_rps=0.5`（每2秒1请求）、`_CONCURRENCY=3`，远低于付费API承受能力
2. **逐条数据库写入**：`append_result_data` 每条结果独立事务，50个样本产生50次独立session/commit
3. **CPU操作阻塞事件循环**：PIL图像渲染（10-50ms）、GIF编码（50-200ms）、Base64编码在asyncio主线程同步执行

当前架构：static_detector.py / dynamic_detector.py → DataProcessor → ResultDB（SQLAlchemy async session），检测循环使用 asyncio.Semaphore + RateLimiter 控制并发。

## Goals / Non-Goals

**Goals:**
- 将检测吞吐量提升 5-10 倍（通过调整并发参数和速率限制）
- 将数据库写入开销降低 80%+（通过批量写入）
- 消除CPU密集操作对事件循环的阻塞（通过线程池卸载）

**Non-Goals:**
- 不改变检测算法逻辑（SDPJ Algorithm 1/2 的步骤和流程不变）
- 不改变数据库表结构（不新增表、不修改字段）
- 不引入多进程（ProcessPoolExecutor），因为CPU操作短暂且频繁，序列化开销不划算
- 不改变 LLMService 的重试策略（tenacity 配置保持不变）
- 不改变 RateLimiter 的实现逻辑（只调参数）

## Decisions

### 决策1：并发参数调整策略

**选择**：`_CONCURRENCY` 3→10，`_BATCH_SIZE` 50→100，`max_rps` 默认值 0.5→2.0

**理由**：
- 规格文档（SDPJDetector.md）明确记载原始设计为 `asyncio.Semaphore(10)`，后因429问题降为3，现在有了四层防线架构（RateLimiter + Semaphore + tenacity重试 + Retry-After头提取），可以安全地恢复到10
- `max_rps=2.0` 对应 120 RPM，匹配主流付费API限额（如 OpenAI Tier1 = 500 RPM，DeepSeek = 100+ RPM）
- `max_rps` 仍作为函数参数暴露，调用方可按API配额自行调整

**备选方案**：动态自适应速率（根据429响应自动调整max_rps）——实现复杂度高，当前四层防线已足够，留作后续优化

### 决策2：批量写入的实现层级

**选择**：在 ResultDB 层新增 `append_result_data_batch`，使用 SQLAlchemy `session.add_all` + 单次 `flush`

**理由**：
- 当前 `append_result_data` 每次调用都创建新 session、检查 report 存在性、生成 ID、add + flush
- 批量版本在单次 session 中完成所有操作，仅一次 flush，事务开销从 O(n) 降为 O(1)
- report 存在性检查在批量入口做一次即可，无需每条重复检查

**调用方改造**：
- `static_detector.py` 的 `_process` 函数：收集批量结果到列表，每批 gather 完成后一次性调用 `append_result_data_batch`
- `dynamic_detector.py`：逐条处理改为收集后批量写入

**备选方案**：在 DataProcessor 层做内存缓冲 + 定时刷盘——增加复杂度且可能丢失数据，不如每批gather后立即批量写入简单可靠

### 决策3：CPU卸载的线程池策略

**选择**：全局 `ThreadPoolExecutor(max_workers=4)`，封装 `run_cpu()` 异步工具函数

**理由**：
- `max_workers=4` 匹配典型CPU核心数，避免过多线程切换开销
- 全局单例避免重复创建销毁
- 封装为 `run_cpu(func, *args)` 简化调用，隐藏 `run_in_executor` 细节

**需要异步化的操作**（仅耗时 > 1ms 的）：
- `_prepare_poc` 中的 `construct_multimodal_sample`（PIL渲染，10-200ms）
- `_prepare_poc` 中的 Base64 编码（对图像/音频二进制数据，1-5ms）
- `_prepare_poc` 中的 `construct_encoded_sample`（编码转换，<1ms，可不同步）

**不需要异步化的操作**：
- `result_parser.py` 的 JSON 解析（<0.1ms，executor调度开销反而更大）
- 简单字符串拼接

**备选方案**：ProcessPoolExecutor——pickle序列化开销可能比计算本身还慢，不适用于短暂频繁的CPU操作

### 决策4：`_prepare_poc` 改为异步

**选择**：新增 `async _prepare_poc_async()` 函数，内部对耗时操作调用 `run_cpu()`

**理由**：
- 保持原 `_prepare_poc` 同步版本不变（可能有其他调用方），新增异步版本供检测循环使用
- 实际上当前只有 `_check` 和 `_process` 调用 `_prepare_poc`，但保持向后兼容更安全

## Risks / Trade-offs

- **[API 429 风险]** → 并发度提升后可能更频繁触发限流 → 四层防线架构（RateLimiter + Semaphore + tenacity + Retry-After）已覆盖；`max_rps` 作为参数暴露，用户可按API配额调低
- **[线程安全]** → `run_in_executor` 中的函数不能访问 asyncio 非线程安全对象 → `_prepare_poc_async` 中仅调用 DataProcessor 的同步方法（`construct_multimodal_sample`、`construct_encoded_sample`），这些方法不涉及 asyncio 对象，线程安全
- **[批量写入部分失败]** → 批量写入中某条数据异常可能导致整批回滚 → 当前场景下数据均由算法生成，格式可控，异常概率极低；若发生则整批重试
- **[内存占用]** → 批量收集结果在内存中暂存 → 每批最多100条，每条含文本字段，内存占用可忽略（<1MB）
