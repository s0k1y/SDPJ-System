## Why

当前检测进度仅展示已处理/总量的计数信息，用户无法预估检测何时完成。PoC 池选择阶段存在早停机制导致 `processed/total` 不能反映真实进度，静态检测阶段缺少时间估算，动态检测阶段完全没有进度回调。用户在长时间检测中缺乏预期管理，体验较差。

## What Changes

- PoC 池选择阶段：在现有 `progress_callback` 中扩展传递 subtype 维度的统计信息（当前有效计数、目标计数、处理速度），并在 `task_queue_manager` 中记录时间戳，由 `query_detection_progress` 计算基于里程碑法的 ETA
- 静态检测阶段：在 `task_queue_manager` 中为每个 task 记录时间戳与滑动窗口处理速度，由 `query_detection_progress` 计算基于剩余量/速度的 ETA
- 动态检测阶段：为 `run_dynamic_detection` 添加 `dynamic_progress_callback`，传递当前处理样本索引/总合规样本数/平均迭代次数，由 `query_detection_progress` 计算基于样本级速度的 ETA
- `query_detection_progress` 返回结构新增 `eta_seconds` 和 `stage_info` 字段

## Capabilities

### New Capabilities

- `detection-eta`: 检测任务预计剩余时间计算能力，覆盖 PoC 池选择（里程碑法+动态总量+时间预测）、静态检测（滑动窗口速度法）、动态检测（样本级进度回调+速度法）三个阶段

### Modified Capabilities

- `TaskQueueManager`: 新增时间戳字段存储（start_time、last_update_time）、subtype 统计存储、滑动窗口速度记录、动态检测进度存储
- `SDPJDetector`: `select_poc_pool` 的 `progress_callback` 签名扩展传递 subtype 统计；`run_dynamic_detection` 新增 `dynamic_progress_callback` 参数
- `StateScheduler`: `query_detection_progress` 返回结构新增 `eta_seconds`、`stage_info` 字段

## Impact

- **代码变更**：
  - `sdpj/core/task_queue_manager.py`：扩展 `_poc_progress` 和 `_task_progress` 数据结构，新增 `_dynamic_progress` 存储
  - `sdpj/core/task_queue_manager_interface.py`：更新接口类型定义
  - `sdpj/core/sdpj_detector/static_detector.py`：修改 `select_poc_pool` 的回调签名和调用方式
  - `sdpj/core/sdpj_detector/dynamic_detector.py`：新增 `dynamic_progress_callback` 参数及内部调用
  - `sdpj/core/sdpj_detector_interface.py`：更新接口签名
  - `sdpj/control/state_scheduler.py`：修改回调桥接逻辑，扩展 `query_detection_progress` 返回结构
- **API 变更**：`query_detection_progress` 返回的 JSON 结构新增字段（向后兼容，新增字段不影响现有消费者）
- **依赖**：无新增外部依赖，仅使用 Python 标准库 `time` 模块
