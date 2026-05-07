## Context

当前 LLM 调用速率控制参数 `max_rps` 和 `_CONCURRENCY` 在检测算法层硬编码，无法适配不同 API 提供商的限额差异。速率限制属于适配器的能力属性（与 `timeout` 同类），应在适配器配置中声明。

现有调用链：`适配器JSON配置 → loader.py → LLMAdapter → LLMAdapterLib → LLMRegistry → state_scheduler.py → SDPJDetector`

规格文档 SDPJDetector.md 第 291-320 行与代码实现不一致（"滑动窗口"vs 令牌桶、参数默认值不同），需同步。

## Goals / Non-Goals

**Goals:**
- 适配器 JSON 配置支持声明 `max_rps` 和 `max_concurrency` 建议值
- 建议值沿调用链传递到检测算法层，替代硬编码默认值
- 调用方仍可覆盖建议值（建议值不是硬性限制）
- 规格文档与代码实现保持一致

**Non-Goals:**
- 不实现动态自适应限流（探测 429 后自动调速），因其探测本身代价高且多协程互相干扰
- 不修改 RateLimiter 算法本身（保持令牌桶实现）
- 不修改 `max_rps` / `_CONCURRENCY` 在检测算法中的使用方式（仍是 RateLimiter + Semaphore）

## Decisions

### D1: 速率字段存储位置 — 存入 LLMAdapter 实例的 metadata

**选择**: 在 LLMAdapter 构造时接收 `max_rps` / `max_concurrency`，通过 `get_metadata()` 暴露。

**备选**: 在 LLMAdapterLib 中单独维护 rate limit 字典。

**理由**: 与 `timeout` 字段处理方式一致，适配器是最了解 API 限速能力的实体。避免在 LLMAdapterLib 中维护与适配器脱节的平行数据结构。

### D2: 参数语义 — 建议值而非硬性限制

**选择**: `max_rps` / `max_concurrency` 为"建议值"（suggested values），调用方可覆盖。

**备选**: 强制使用适配器配置的值，禁止覆盖。

**理由**: 检测算法的调用方（如 state_scheduler）可能根据系统负载、并发任务数等因素需要降低速率。建议值语义保留了灵活性。

### D3: _CONCURRENCY 改为函数参数

**选择**: 将 `_CONCURRENCY` 模块常量改为 `max_concurrency` 函数参数，默认值保持 10。

**备选**: 保留模块常量，新增一个全局配置机制。

**理由**: 函数参数是最简单的方式，与 `max_rps` 已有的参数传递机制一致。模块常量不适合按适配器动态调整。

### D4: 规格文档同步策略 — 直接更新现有描述

**选择**: 直接更新 SDPJDetector.md 第 291-320 行，使描述与代码实现一致。

**备选**: 保留规格原文，在末尾追加勘误说明。

**理由**: 规格应反映真实实现，保持单一事实来源。追加勘误增加认知负担。

## Risks / Trade-offs

- **[向后兼容]** 适配器 JSON 配置新增 `max_rps` / `max_concurrency` 为可选字段 → 不填时使用保守默认值（0.5 / 3），确保现有配置不触发 429
- **[过度限速]** 用户可能设置过低的建议值 → 默认值保守（0.5 / 3）即可安全运行，用户按需调高
- **[规格不一致复发]** 代码修改后规格可能再次过时 → 本次变更同时更新规格和代码，建立一致基线
