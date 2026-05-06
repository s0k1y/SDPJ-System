## 1. 后端核心实现

- [ ] 1.1 在 StateScheduler 中新增私有方法 `_cleanup_task_queue_after_report_delete(target_id, granularity)`，实现按粒度清理任务队列逻辑
- [ ] 1.2 修改 StateScheduler.delete_report()，在删除报告成功后调用 `_cleanup_task_queue_after_report_delete`

## 2. 验证

- [ ] 2.1 启动系统，创建检测任务并等待完成，在 Reports 页面删除任务组报告，验证 Dashboard 任务队列同步清空
- [ ] 2.2 创建检测任务，在 Reports 页面删除单个任务报告，验证 Dashboard 任务队列中对应任务消失
- [ ] 2.3 创建检测任务（含 pending/running 状态），在 Reports 页面删除任务组报告，验证运行中任务被正确取消和移除
