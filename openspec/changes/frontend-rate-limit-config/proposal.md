## Why

规格文档 SDPJDetector.md 第 340-345 行定义了适配器 JSON 配置可声明 `max_rps` 和 `max_concurrency` 建议值，后端 `loader.py` 和 `state_scheduler.py` 已实现读取和传递逻辑，但前端 UI 完全缺失：适配器配置模板不含速率字段，检测启动表单无覆盖入口，用户无法通过界面配置或调整速率限制参数。

## What Changes

- 适配器配置模板（PrivateConfig.vue）所有模板增加 `max_rps`（默认 0.5）和 `max_concurrency`（默认 3）字段
- 检测启动表单（DetectionForm.vue）步骤2增加可选的速率限制覆盖区域，允许用户在启动检测时覆盖适配器建议值
- 后端请求模型（DetectionStartRequest）增加可选字段 `max_rps`（float, Optional）和 `max_concurrency`（int, Optional）
- 后端调度层（state_scheduler.py）`start_detection()` 将用户覆盖值传递到检测任务参数

## Capabilities

### New Capabilities

- `frontend-rate-limit-ui`: 前端适配器配置模板和检测启动表单中支持速率限制参数的配置与覆盖

### Modified Capabilities

## Impact

- 前端文件：`PrivateConfig.vue`（模板定义）、`DetectionForm.vue`（表单字段与提交逻辑）
- 后端文件：`sdpj/ui/webui/backend/schemas/detection.py`（请求模型）、`sdpj/control/state_scheduler.py`（参数传递）
- 向后兼容：新增字段均为可选，未填时使用适配器建议值或保守默认值
