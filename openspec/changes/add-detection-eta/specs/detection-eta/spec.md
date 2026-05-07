## ADDED Requirements

### Requirement: PoC 池选择阶段 ETA 计算
系统 SHALL 在 PoC 池选择阶段计算并返回预计剩余时间（ETA）。ETA 计算基于 subtype 里程碑法：追踪每个 subtype 的当前有效计数与目标计数，对未达标 subtype 预估剩余时间，取最大值作为全局 ETA。

#### Scenario: 所有 subtype 已达标
- **WHEN** PoC 池选择阶段所有 subtype 的 `event_set` 均为 True
- **THEN** 系统 SHALL 返回 `eta_seconds` 为 0，`stage_info` 包含 `"已完成"`

#### Scenario: 部分 subtype 未达标且数据充足
- **WHEN** PoC 池选择阶段存在未达标 subtype，且已收到至少 3 次进度回调
- **THEN** 系统 SHALL 对每个未达标 subtype 计算 `(target - current) / subtype_speed`，取最大值作为 `eta_seconds`，`stage_info` 包含 `remaining_subtypes` 列表

#### Scenario: 数据不足无法估算
- **WHEN** PoC 池选择阶段进度回调次数不足 3 次
- **THEN** 系统 SHALL 返回 `eta_seconds` 为 -1，`stage_info` 包含 `"计算中..."`

#### Scenario: 某 subtype 迟迟不达标
- **WHEN** 某未达标 subtype 的速度低于 0.01 个/秒
- **THEN** 系统 SHALL 在 `stage_info` 中标注该 subtype 为 `"较难获取"`

### Requirement: 静态检测阶段 ETA 计算
系统 SHALL 在静态检测阶段基于滑动窗口速度法计算每个 task 的 ETA，取所有未完成 task 中最大的 ETA 作为全局 ETA。

#### Scenario: 单个 task 正在执行
- **WHEN** 静态检测阶段某个 task 正在执行，且已有至少 2 次 batch 完成的速度数据
- **THEN** 系统 SHALL 计算该 task 的 `eta_seconds = (total - processed) / avg_speed`，其中 `avg_speed` 为最近 5 次 batch 速度的算术平均

#### Scenario: 多个 task 并行执行
- **WHEN** 静态检测阶段有多个 task 并行执行
- **THEN** 系统 SHALL 取所有未完成 task 中最大的 `eta_seconds` 作为该阶段的全局 ETA

#### Scenario: task 刚开始无速度数据
- **WHEN** 某个 task 刚开始执行，尚无 batch 完成的速度数据
- **THEN** 系统 SHALL 返回该 task 的 `eta_seconds` 为 -1

### Requirement: 动态检测阶段进度回调与 ETA 计算
系统 SHALL 在动态检测阶段提供进度回调，传递当前已处理的合规样本数、总合规样本数和平均迭代次数，并基于样本级速度计算 ETA。

#### Scenario: 动态检测进度更新
- **WHEN** 动态检测阶段处理完一个合规样本
- **THEN** 系统 SHALL 调用 `dynamic_progress_callback(processed, total_compliant, avg_iterations)`，其中 `processed` 为已处理合规样本数，`total_compliant` 为总合规样本数，`avg_iterations` 为当前平均迭代次数

#### Scenario: 动态检测 ETA 计算
- **WHEN** 动态检测阶段已有至少 2 次进度回调
- **THEN** 系统 SHALL 计算 `eta_seconds = (total_compliant - processed) / sample_speed`，其中 `sample_speed` 基于滑动窗口计算

#### Scenario: 动态检测数据不足
- **WHEN** 动态检测阶段进度回调次数不足 2 次
- **THEN** 系统 SHALL 返回 `eta_seconds` 为 -1

### Requirement: query_detection_progress 返回结构扩展
系统 SHALL 在 `query_detection_progress` 返回的每个 group 中新增 `eta_seconds` 和 `stage_info` 字段。

#### Scenario: PoC 池选择阶段返回 ETA
- **WHEN** 查询检测进度时 PoC 池选择阶段正在进行
- **THEN** 返回结构中该 group 的 `eta_seconds` 为 PoC 池选择阶段的预估剩余秒数，`stage_info` 包含 `{"stage": "poc_selecting", "remaining_subtypes": [...], "estimated_needed": N}`

#### Scenario: 静态检测阶段返回 ETA
- **WHEN** 查询检测进度时静态检测阶段正在进行（PoC 选择已完成）
- **THEN** 返回结构中该 group 的 `eta_seconds` 为静态检测阶段的预估剩余秒数，`stage_info` 包含 `{"stage": "static_detecting", "tasks_remaining": N}`

#### Scenario: 动态检测阶段返回 ETA
- **WHEN** 查询检测进度时动态检测阶段正在进行
- **THEN** 返回结构中该 group 的 `eta_seconds` 为动态检测阶段的预估剩余秒数，`stage_info` 包含 `{"stage": "dynamic_detecting", "avg_iterations": F, "samples_remaining": N}`

#### Scenario: 检测已完成
- **WHEN** 查询检测进度时所有阶段均已完成
- **THEN** 返回结构中该 group 的 `eta_seconds` 为 0，`stage_info` 包含 `{"stage": "completed"}`

### Requirement: 时间格式化工具函数
系统 SHALL 提供 `format_eta` 工具函数，将秒数格式化为人类可读的时间字符串。

#### Scenario: 秒级时间
- **WHEN** 输入秒数小于 60
- **THEN** 输出格式为 `"{N}秒"`，如 `"45秒"`

#### Scenario: 分钟级时间
- **WHEN** 输入秒数大于等于 60 且小于 3600
- **THEN** 输出格式为 `"{M}分{S}秒"`，如 `"5分30秒"`

#### Scenario: 小时级时间
- **WHEN** 输入秒数大于等于 3600
- **THEN** 输出格式为 `"{H}小时{M}分"`，如 `"1小时30分"`

#### Scenario: 无效时间
- **WHEN** 输入秒数为负数
- **THEN** 输出 `"计算中..."`

## MODIFIED Requirements

### Requirement: TaskQueueManager 进度数据存储
系统 SHALL 在 `TaskQueueManager` 中扩展进度数据存储结构，新增时间戳和速度相关字段。

#### Scenario: PoC 进度数据结构
- **WHEN** 调用 `update_poc_progress` 时
- **THEN** 存储的进度数据 SHALL 包含 `start_time`（monotonic 时间戳）、`last_update_time`、`subtype_stats`（每个 subtype 的 `{current, target, event_set, speed}` 字典）、`remaining_subtypes` 列表

#### Scenario: Task 进度数据结构
- **WHEN** 调用 `update_task_progress` 时
- **THEN** 存储的进度数据 SHALL 包含 `start_time`（monotonic 时间戳）、`last_update_time`、`recent_speeds`（最近 5 次 batch 速度列表）

#### Scenario: 动态检测进度数据结构
- **WHEN** 调用 `update_dynamic_progress` 时
- **THEN** 系统 SHALL 在 `_dynamic_progress[task_group_id]` 中存储 `{processed, total, avg_iterations, start_time, last_update_time, recent_speeds}`

### Requirement: SDPJDetector 进度回调签名扩展
系统 SHALL 扩展 `select_poc_pool` 的 `progress_callback` 签名，新增第 5 个参数 `subtype_stats`。

#### Scenario: progress_callback 调用
- **WHEN** `select_poc_pool` 内部调用 `progress_callback` 时
- **THEN** 回调签名 SHALL 为 `(processed, total, found, score_counts, subtype_stats)`，其中 `subtype_stats` 为 `{subtype: {current: int, target: int, event_set: bool}}` 字典

#### Scenario: 向后兼容
- **WHEN** 外部调用方使用旧的 4 参数回调
- **THEN** 系统 SHALL 通过默认值 `subtype_stats=None` 保持兼容，不引发 TypeError

### Requirement: run_dynamic_detection 新增进度回调参数
系统 SHALL 为 `run_dynamic_detection` 新增 `dynamic_progress_callback` 可选参数。

#### Scenario: dynamic_progress_callback 调用
- **WHEN** 动态检测阶段处理完一个合规样本
- **THEN** 系统 SHALL 调用 `dynamic_progress_callback(processed, total_compliant, avg_iterations)`

#### Scenario: dynamic_progress_callback 为 None
- **WHEN** `dynamic_progress_callback` 参数未提供或为 None
- **THEN** 系统 SHALL 正常执行动态检测，不调用回调
