## Context

当前系统中，Reports页面删除检测报告的调用链为：`Reports.vue → DELETE /api/reports/{target_id} → StateScheduler.delete_report() → ReportManager.delete_report() → DataProcessor.delete_*()`。该链路仅清理数据库记录，未同步清理TaskQueueManager内存中的任务条目。

Dashboard任务队列通过5秒轮询`GET /api/detection/progress`从TaskQueueManager.get_queue_view()获取数据。由于内存中残留已删除的任务条目，导致Dashboard持续显示已删除的任务/任务组。

已有参考实现：`StateScheduler.cancel_task_group()`已实现"取消任务→移除任务→删除报告"的完整流程，本次变更为其反向操作（从删除报告触发，清理任务队列）。

## Goals / Non-Goals

**Goals:**
- 删除报告后，TaskQueueManager内存中对应的任务条目同步清理
- 非终态(pending/running)任务先cancel再remove，避免残留运行中的协程
- 终态(completed/failed/cancelled)任务直接remove
- Dashboard通过现有轮询机制自动反映变更

**Non-Goals:**
- 不修改前端代码（Dashboard已有轮询机制）
- 不修改DataProcessor层（数据库级联删除已有实现）
- 不处理report/result_data粒度的任务队列清理（这些粒度不涉及任务本身）
- 不修改cancel_task_group的现有逻辑

## Decisions

### D1: 在StateScheduler.delete_report中增加后置清理逻辑

**选择**: 在delete_report成功后调用新增的私有方法`_cleanup_task_queue_after_report_delete`

**替代方案**: 在ReportManager.delete_report中回调StateScheduler → 违反层级依赖方向（执行逻辑层不应依赖控制层）

**理由**: StateScheduler是控制层，同时持有ReportManager和TaskQueueManager的引用，是协调两者的正确位置。这与cancel_task_group中协调两者的模式一致。

### D2: 按granularity区分清理范围

- `task_group`: 清理该task_group_id下所有任务
- `task`: 清理该task_id对应的单个任务
- `report`/`result_data`: 不清理（报告和结果数据是任务执行后的产物，删除它们不应影响任务队列）

### D3: 清理顺序——先cancel非终态任务再remove

**选择**: 对pending/running任务先cancel_task（设置CANCELLED状态并持久化），再remove_task（从内存字典移除）

**替代方案**: 直接remove_task不cancel → 如果任务正在被消费者协程执行，dequeue时可能已取出但未完成，导致执行结果无法回写

**理由**: cancel_task会将任务状态设为CANCELLED，消费者在execute_detection_task开头检查状态会跳过已取消任务，确保运行中的协程不会继续执行。

## Risks / Trade-offs

- [cancel_task的_persist_status可能因数据库记录已被DataProcessor删除而失败] → _persist_status已有try/except pass兜底，不影响内存清理
- [删除报告时任务正在running，cancel后检测协程可能仍在执行一小段] → execute_detection_task在执行中和执行后都会检查CANCELLED状态，影响可控
- [task粒度删除后，同组其他任务仍在队列中但数据库中任务组已级联删除] → 这是合理的，因为用户只删除了单个报告，不应影响同组其他任务
