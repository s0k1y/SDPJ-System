## MODIFIED Requirements

### Requirement: 删除检测报告后同步清理任务队列
StateScheduler.delete_report 在删除报告成功后，SHALL 根据 granularity 参数同步清理 TaskQueueManager 中对应的任务条目，确保 Dashboard 任务队列不再显示已删除报告对应的任务。

#### Scenario: 删除任务组级报告后清理整个任务组
- **WHEN** 用户以 granularity="task_group" 删除报告且删除成功
- **THEN** StateScheduler SHALL 从 TaskQueueManager 中找到该 task_group_id 下的所有任务，对非终态(pending/running)任务先 cancel_task 再 remove_task，对终态(completed/failed/cancelled)任务直接 remove_task

#### Scenario: 删除任务级报告后清理单个任务
- **WHEN** 用户以 granularity="task" 删除报告且删除成功
- **THEN** StateScheduler SHALL 从 TaskQueueManager 中找到该 task_id 对应的任务，对非终态任务先 cancel_task 再 remove_task，对终态任务直接 remove_task

#### Scenario: 删除报告级或结果数据级报告不影响任务队列
- **WHEN** 用户以 granularity="report" 或 granularity="result_data" 删除报告且删除成功
- **THEN** StateScheduler SHALL 不清理 TaskQueueManager 中的任何任务条目

#### Scenario: 删除报告失败时不清理任务队列
- **WHEN** 用户删除报告且删除失败
- **THEN** StateScheduler SHALL 不清理 TaskQueueManager 中的任何任务条目

#### Scenario: Dashboard 任务队列自动反映变更
- **WHEN** 报告删除后任务队列已被清理
- **THEN** Dashboard 通过现有 5 秒轮询机制获取最新队列视图，不再显示已删除报告对应的任务/任务组
