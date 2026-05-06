## Why

当用户在Reports页面删除任务/任务组检测报告时，仅清理了数据库中的记录，但TaskQueueManager内存中的任务条目仍然残留。这导致Dashboard任务队列持续显示已被删除的任务/任务组，造成数据不一致和用户困惑。需要在删除报告时同步清理任务队列中的对应条目。

## What Changes

- StateScheduler.delete_report() 在删除报告成功后，根据granularity同步清理TaskQueueManager中对应的任务条目
- granularity为task_group时：移除该任务组下所有任务（非终态先cancel再remove，终态直接remove）
- granularity为task时：移除该任务（非终态先cancel再remove，终态直接remove）
- granularity为report/result_data时：不涉及任务队列清理（这些是任务执行后的产物，任务本身可能仍在队列中）

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `StateScheduler`: delete_report方法需增加任务队列清理后置逻辑，确保删除报告后任务队列同步更新

## Impact

- **代码**：`sdpj/control/state_scheduler.py` 的 `delete_report` 方法
- **API**：DELETE `/api/reports/{target_id}` 行为变更——删除报告后任务队列同步清理
- **前端**：Dashboard任务队列无需修改，已有5秒轮询机制自动刷新
- **依赖**：依赖TaskQueueManager的cancel_task和remove_task方法（已存在）
