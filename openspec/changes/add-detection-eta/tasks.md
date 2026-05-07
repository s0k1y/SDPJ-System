## 1. 基础设施：时间格式化与数据结构扩展

- [ ] 1.1 在 `sdpj/infrastructure/utils/` 中新增 `eta_formatter.py`，实现 `format_eta(seconds: float) -> str` 函数
- [ ] 1.2 扩展 `task_queue_manager.py` 的 `update_poc_progress` 方法，支持存储 `start_time`、`last_update_time`、`subtype_stats`、`remaining_subtypes` 字段
- [ ] 1.3 扩展 `task_queue_manager.py` 的 `update_task_progress` 方法，支持存储 `start_time`、`last_update_time`、`recent_speeds` 字段
- [ ] 1.4 在 `task_queue_manager.py` 中新增 `_dynamic_progress` 字典及 `update_dynamic_progress`、`get_dynamic_progress`、`clear_dynamic_progress` 方法
- [ ] 1.5 更新 `task_queue_manager_interface.py` 接口定义，新增 `update_dynamic_progress`、`get_dynamic_progress`、`clear_dynamic_progress` 方法签名

## 2. PoC 池选择阶段 ETA

- [ ] 2.1 修改 `static_detector.py` 的 `select_poc_pool` 函数，在 `progress_callback` 调用中新增第 5 个参数 `subtype_stats`（包含每个 subtype 的 current/target/event_set）
- [ ] 2.2 修改 `state_scheduler.py` 的 `_poc_progress_cb` 回调，接收并存储 `subtype_stats` 到 `task_queue_manager`
- [ ] 2.3 在 `state_scheduler.py` 的 `_poc_progress_cb` 中记录 `start_time`（首次回调时）和 `last_update_time`（每次回调时）
- [ ] 2.4 在 `state_scheduler.py` 的 `query_detection_progress` 中实现 PoC 池选择阶段 ETA 计算逻辑（里程碑法 + 动态总量 + 时间预测）

## 3. 静态检测阶段 ETA

- [ ] 3.1 修改 `state_scheduler.py` 的 `_task_progress_cb` 回调，记录 `start_time`（首次回调时）、`last_update_time` 和 `recent_speeds`（每次回调时计算当前 batch 速度并追加）
- [ ] 3.2 在 `state_scheduler.py` 的 `query_detection_progress` 中实现静态检测阶段 ETA 计算逻辑（滑动窗口速度 × 剩余量）

## 4. 动态检测阶段进度回调与 ETA

- [ ] 4.1 修改 `dynamic_detector.py` 的 `run_dynamic_detection` 函数签名，新增 `dynamic_progress_callback` 可选参数
- [ ] 4.2 在 `dynamic_detector.py` 中实现合规样本数统计逻辑（遍历静态结果计算 `total_compliant`）
- [ ] 4.3 在 `dynamic_detector.py` 中每处理完一个合规样本后调用 `dynamic_progress_callback(processed, total_compliant, avg_iterations)`
- [ ] 4.4 修改 `sdpj_detector_interface.py` 的 `run_dynamic_detection` 签名，新增 `dynamic_progress_callback` 参数
- [ ] 4.5 修改 `state_scheduler.py` 的 `execute_detection_task`，构建 `_dynamic_progress_cb` 回调并传递给 `run_dynamic_detection`
- [ ] 4.6 在 `state_scheduler.py` 的 `query_detection_progress` 中实现动态检测阶段 ETA 计算逻辑（样本级速度法）

## 5. query_detection_progress 返回结构扩展

- [ ] 5.1 在 `query_detection_progress` 返回的 group 结构中新增 `eta_seconds` 字段（float，-1 表示无法估算，0 表示已完成）
- [ ] 5.2 在 `query_detection_progress` 返回的 group 结构中新增 `stage_info` 字段（dict，包含 stage/remaining_subtypes/estimated_needed 等信息）
- [ ] 5.3 在 `execute_detection_task` 的 finally 块中清理 `_dynamic_progress`

## 6. 验证

- [ ] 6.1 为 `format_eta` 编写单元测试
- [ ] 6.2 为 PoC 池选择阶段 ETA 计算逻辑编写单元测试
- [ ] 6.3 为静态检测阶段 ETA 计算逻辑编写单元测试
- [ ] 6.4 为动态检测阶段进度回调与 ETA 计算逻辑编写单元测试
- [ ] 6.5 运行全量测试确保无回归
