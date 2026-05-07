## 1. 适配器配置模板增加速率限制字段

- [x] 1.1 更新 `PrivateConfig.vue` — 3 个适配器模板（openai/anthropic/custom）增加 `max_rps: 0.5` 和 `max_concurrency: 3` 字段；清理 8 个未暴露的冗余模板
- [x] 1.2 更新 `PrivateConfig.vue` — 模板指南描述中补充速率限制字段说明

## 2. 检测启动表单增加速率限制覆盖

- [x] 2.1 更新 `DetectionForm.vue` — 步骤2增加可折叠"高级设置"区域，包含 `max_rps`（el-input-number, step=0.1, min=0.1）和 `max_concurrency`（el-input-number, step=1, min=1）输入框
- [x] 2.2 更新 `DetectionForm.vue` — form 数据增加 `max_rps` 和 `max_concurrency` 可选字段
- [x] 2.3 更新 `DetectionForm.vue` — 步骤3确认页面增加速率限制信息展示
- [x] 2.4 更新 `DetectionForm.vue` — handleSubmit 中条件性将 `max_rps`/`max_concurrency` 加入 payload

## 3. 后端请求模型与调度层支持

- [x] 3.1 更新 `sdpj/ui/webui/backend/schemas/detection.py` — `DetectionStartRequest` 增加 `max_rps: Optional[float] = None` 和 `max_concurrency: Optional[int] = None`
- [x] 3.2 更新 `sdpj/control/state_scheduler.py` — `start_detection()` 将 `max_rps`/`max_concurrency` 从 config_data 传递到任务参数
- [x] 3.3 更新 `sdpj/control/state_scheduler.py` — `execute_detection_task()` 优先使用用户覆盖值，无覆盖时使用适配器建议值
