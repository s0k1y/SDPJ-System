## Context

当前系统检测进度仅展示 `processed/total` 计数信息，缺少时间维度的预估。三个检测阶段的进度追踪能力参差不齐：

- **PoC 池选择**：有 `progress_callback(processed, total, found, score_counts)`，但存在 subtype 独立早停机制，`processed/total` 不反映真实进度
- **静态检测**：有 `task_progress_callback(task_id, processed, total)`，无早停，线性增长，最易预估
- **动态检测**：无任何进度回调，嵌套迭代结构（外层遍历 PoC 池 × 内层 max_iterations），迭代次数不确定

所有进度数据存储在 `TaskQueueManager` 的内存字典中（`_poc_progress`、`_task_progress`），由 `StateScheduler.query_detection_progress` 汇总后返回给前端。

## Goals / Non-Goals

**Goals:**

- PoC 池选择阶段：基于 subtype 里程碑 + 动态总量 + 纯时间预测三种思路结合，提供准确的 ETA
- 静态检测阶段：基于滑动窗口速度 × 剩余量计算 ETA
- 动态检测阶段：添加进度回调，基于样本级速度计算 ETA
- `query_detection_progress` 返回结构新增 `eta_seconds` 和 `stage_info` 字段
- 时间格式化工具函数

**Non-Goals:**

- 不修改前端 UI（仅提供后端数据）
- 不持久化 ETA 历史数据
- 不实现跨任务组的全局 ETA 汇总
- 不处理缓存命中场景下的 ETA（缓存命中时 PoC 选择秒级完成，无需 ETA）

## Decisions

### D1: PoC 池选择阶段 ETA — 三思路结合

**选择**：里程碑法（追踪 subtype 达标进度）+ 动态总量法（预估实际需要处理的样本数）+ 纯时间预测（基于处理速度估算剩余时间）

**方案**：

1. 扩展 `progress_callback` 签名为 `(processed, total, found, score_counts, subtype_stats)`，其中 `subtype_stats` 包含每个 subtype 的 `{current, target, event_set}` 信息
2. 在 `task_queue_manager._poc_progress` 中新增字段：`start_time`、`last_update_time`、`subtype_stats`、`remaining_subtypes`
3. ETA 计算逻辑：
   - 若所有 subtype 的 `event_set=True`，ETA=0（已完成）
   - 否则，对未达标 subtype：`remaining_time = (target - current) / subtype_speed`，取 max 作为全局 ETA
   - 若数据不足（<3 次回调），显示"计算中..."

**替代方案**：仅用 `processed/total` 线性外推 → 因早停机制导致严重偏差，否决

### D2: 静态检测阶段 ETA — 滑动窗口速度法

**选择**：在 `task_queue_manager._task_progress` 中记录 `start_time`、`last_update_time`、`recent_speeds`（最近 5 次 batch 的处理速度），ETA = `(total - processed) / avg_speed`

**方案**：

1. 扩展 `_task_progress[task_id]` 数据结构，新增 `start_time`、`last_update_time`、`recent_speeds` 列表
2. 每次 `task_progress_callback` 调用时，计算当前 batch 速度并追加到 `recent_speeds`（保留最近 5 个）
3. ETA = `(total - processed) / (sum(recent_speeds) / len(recent_speeds))`
4. 多 task 汇总：取所有未完成 task 中最大的 ETA

**替代方案**：全局平均速度 → 初期波动大，否决

### D3: 动态检测阶段 ETA — 添加进度回调

**选择**：为 `run_dynamic_detection` 添加 `dynamic_progress_callback(processed, total, avg_iterations)` 参数

**方案**：

1. 在 `dynamic_detector.py` 中，先遍历静态检测结果统计合规样本数 `total_compliant`
2. 每处理完一个合规样本后调用回调：`callback(processed, total_compliant, avg_iterations_so_far)`
3. 在 `task_queue_manager` 中新增 `_dynamic_progress[task_group_id]` 存储
4. ETA = `(total - processed) / speed`，其中 speed 基于滑动窗口计算
5. 额外信息：`avg_iterations` 可帮助用户理解检测深度

**替代方案**：经验公式（动态耗时 ≈ 静态耗时 × K）→ K 值因场景差异大，否决

### D4: 时间戳记录方式

**选择**：使用 `time.monotonic()` 记录时间戳

**理由**：不受系统时钟调整影响，适合计算时间差

### D5: 速度计算策略

**选择**：滑动窗口（保留最近 5 个数据点），取算术平均

**理由**：简单、平滑、对近期变化敏感，5 个点足以过滤噪声

### D6: 回调签名兼容性

**选择**：`progress_callback` 新增第 5 个参数 `subtype_stats`，使用默认值 `None` 保持向后兼容

**理由**：避免破坏现有调用点

## Risks / Trade-offs

- **[PoC 选择 ETA 精度]** subtype 速度在初期波动大 → 缓解：数据不足时显示"计算中..."而非具体数字
- **[动态检测 total 预估]** 合规样本数需先遍历静态结果才能确定 → 缓解：遍历开销极小（纯内存操作），不影响性能
- **[回调频率]** 过于频繁的回调可能影响性能 → 缓解：仅在 batch 完成时调用（与现有逻辑一致），不增加额外调用
- **[内存开销]** `_dynamic_progress` 新增存储 → 缓解：每个 task_group 仅一个 dict，开销可忽略
- **[并发安全]** 多协程并发更新进度数据 → 缓解：现有 `_lock` 已保护，新增字段在同一锁范围内
