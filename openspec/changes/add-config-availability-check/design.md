## Context

当前系统允许用户在私有配置页面上传/创建大模型适配器配置文件（JSON），但无法在检测前验证配置是否可用。历史故障表明，`request_format` 与目标 API 不匹配（如 DeepSeek 配了 anthropic 格式）会导致所有 API 调用静默失败，用户难以排查。

现有架构链路：
- 前端 `PrivateConfig.vue` → `detectionConfig('list'|'create'|...)` → 后端 `/api/detection/config` → `StateScheduler.schedule_config_operation()`
- 适配器注册：`LLMAdapterLib.install_adapter()` → `loader.load_adapter_from_config()` → 根据 `request_format` 创建对应 Adapter
- LLM 调用：`LLMService.invoke_llm()` → `LLMServiceInstance.call()` → `Adapter.call()`

## Goals / Non-Goals

**Goals:**
- 提供配置可用性验证 API，实际向目标大模型发送简短测试消息并返回结果
- 前端配置列表增加"测试"操作按钮，展示验证结果（成功/失败/延迟/错误详情）
- 验证过程不触发 FSM 状态转移，不影响系统当前状态

**Non-Goals:**
- 不修改现有检测流程或适配器加载逻辑
- 不在配置创建/保存时自动验证（仅用户手动触发）
- 不验证配置文件格式（已有 validate_file_format）

## Decisions

### 1. 验证方式：临时注册 + 单次调用 + 注销

**选择**：为验证目的临时注册适配器，执行一次简短调用后立即注销。

**理由**：复用现有 `LLMAdapterLib.install_adapter()` + `LLMService.invoke_llm()` 链路，无需为验证场景单独实现 HTTP 调用逻辑。临时注册/注销确保不污染运行中的适配器注册表。

**替代方案**：
- 直接用 httpx/aiohttp 调用 API → 需要重复实现请求格式适配逻辑，违反 DRY
- 复用已注册适配器 → 配置可能尚未注册，且验证不应影响已注册实例

### 2. API 端点：复用 config operation 机制

**选择**：在 `schedule_config_operation` 中新增 `verify` 操作，前端通过 `detectionConfig('verify', { config_id })` 调用。

**理由**：与现有配置操作（create/read/update/delete/list/import/export）保持一致的调用模式，无需新增路由。

### 3. 验证消息内容

**选择**：发送 `system_prompt=""`, `user_message="Hello, respond with exactly: OK"` 作为测试消息。

**理由**：简短、确定性高、token 消耗极低（约 5-10 tokens），且能验证完整的请求/响应链路。

### 4. 超时与重试策略

**选择**：验证调用不重试，超时 30 秒。使用 `asyncio.wait_for` 包裹调用。

**理由**：验证是用户主动触发的即时反馈操作，重试会导致长时间等待。30 秒超时覆盖大多数网络场景。

### 5. 前端验证结果展示

**选择**：使用 `ElMessageBox.alert` 弹窗展示验证结果，包含：状态图标、模型名称、响应延迟、错误信息（如有）。

**理由**：弹窗模式与现有"查看"操作一致，信息展示空间充足。

## Risks / Trade-offs

- **[临时注册副作用]** 临时注册/注销可能在并发场景下与同名适配器冲突 → 使用 UUID 作为临时 model_id 避免冲突
- **[验证消耗 API 额度]** 每次验证会消耗少量 token → 在 UI 上明确提示"将向目标模型发送一条测试消息"
- **[30 秒超时可能不够]** 某些慢速模型可能需要更长时间 → 30 秒对测试消息已足够，超时后返回明确错误
