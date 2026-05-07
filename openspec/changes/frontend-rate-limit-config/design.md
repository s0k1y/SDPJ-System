## Context

后端已实现适配器速率限制建议值的完整链路：`loader.py` 从适配器 JSON 配置读取 `max_rps`/`max_concurrency`，`LLMAdapter.get_metadata()` 暴露这些值，`state_scheduler.py` 的 `execute_detection_task()` 查询适配器建议值并传递到检测器。但前端 UI 完全缺失，用户无法通过界面配置或调整这些参数。

当前前端状态：
- `PrivateConfig.vue` 的 11 个适配器模板均不含 `max_rps`/`max_concurrency` 字段
- `DetectionForm.vue` 检测启动表单无速率控制覆盖入口
- `DetectionStartRequest` 后端请求模型无 `max_rps`/`max_concurrency` 可选字段
- `state_scheduler.py` 的 `start_detection()` 不从 `config_data` 读取用户覆盖值

## Goals / Non-Goals

**Goals:**
- 适配器配置模板增加 `max_rps` 和 `max_concurrency` 字段，用户可在创建/编辑配置时设置
- 检测启动表单增加可选的速率限制覆盖区域，允许用户在启动检测时覆盖适配器建议值
- 后端请求模型和调度层支持接收和传递用户覆盖值
- 速率控制字段在 UI 中有清晰的提示说明，帮助用户理解参数含义和推荐值

**Non-Goals:**
- 不实现动态自适应限流 UI（如根据 429 错误自动调整）
- 不修改 RateLimiter 算法本身
- 不修改检测算法中 `max_rps`/`max_concurrency` 的使用方式
- 不实现速率限制的实时监控仪表盘

## Decisions

### D1: 适配器模板默认值策略 — 按免费 API 保守默认

**选择**: 所有模板默认 `max_rps=0.5`、`max_concurrency=3`（与规格文档 SDPJDetector.md 第 343 行一致）。

**备选**: 不同模板使用不同默认值（如付费 API 模板用更高值）。

**理由**: 保守默认值确保不会意外触发 429，用户按需调高。不同 API 提供商的限额差异大，模板无法预知用户的实际限额。

### D2: 检测启动表单覆盖方式 — 可折叠区域 + 可选字段

**选择**: 在步骤2中增加可折叠的"高级设置"区域，包含 `max_rps` 和 `max_concurrency` 输入框，默认折叠。不填时使用适配器建议值。

**备选**: 始终显示速率控制字段。

**理由**: 速率控制对大多数用户是高级参数，折叠减少认知负担。需要覆盖的用户可展开设置。

### D3: 后端参数传递 — 可选字段透传

**选择**: `DetectionStartRequest` 增加 `max_rps: Optional[float] = None` 和 `max_concurrency: Optional[int] = None`。`start_detection()` 在构造任务参数时，如果用户提供了覆盖值则使用覆盖值，否则由 `execute_detection_task()` 查询适配器建议值。

**备选**: 在 `start_detection()` 中立即查询适配器建议值并合并。

**理由**: 保持建议值查询逻辑集中在 `execute_detection_task()` 中（已实现），避免重复查询。用户覆盖值作为任务参数透传即可。

### D4: 速率限制字段在配置列表中的展示 — 不新增列

**选择**: 不在配置列表表格中新增 `max_rps`/`max_concurrency` 列，仅在查看/编辑配置详情时可见。

**备选**: 在表格中新增速率限制列。

**理由**: 速率限制是次要信息，表格已有多列，新增会显得拥挤。用户需要时可通过"查看"按钮查看完整配置。

## Risks / Trade-offs

- **[用户设置过低值]** 用户可能设置过低的 `max_rps` 导致检测耗时极长 → 默认值保守（0.5/3）即可安全运行，UI 提示推荐值范围
- **[用户设置过高值]** 用户可能设置过高值触发 429 → 后端已有四层防线（RateLimiter + Semaphore + 退避重试 + Retry-After），不会造成系统崩溃
- **[向后兼容]** 新增字段均为可选，现有配置不含这些字段时后端使用保守默认值 → 无迁移风险
