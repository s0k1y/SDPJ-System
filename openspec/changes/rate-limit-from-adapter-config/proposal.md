## Why

当前 LLM 调用的速率限制参数（`max_rps`、`_CONCURRENCY`）在检测算法层硬编码，无法适配不同 API 提供商的限额差异（免费 API 仅 3-10 RPM，付费 API 可达 500+ RPM）。这导致：使用低限额 API 时频繁触发 429，使用高限额 API 时吞吐量远低于实际可承受范围。速率限制属于适配器的能力属性，应与 `timeout` 一样在适配器配置中声明并沿调用链传递。

此外，规格文档 SDPJDetector.md 第 291-320 行描述的 RateLimiter 为"滑动窗口"，但实际实现为令牌桶；参数默认值（max_rps=0.5, _CONCURRENCY=3, _BATCH_SIZE=50）也与代码（max_rps=2.0, _CONCURRENCY=10, _BATCH_SIZE=100）不一致，需要同步。

## What Changes

- 适配器 JSON 配置增加 `max_rps`（建议值，float，默认 0.5）和 `max_concurrency`（建议值，int，默认 3）字段
- `LLMAdapter.get_metadata()` 暴露速率限制建议值
- `LLMAdapterLib.get_adapter_info()` 透传速率限制建议值
- `static_detector.py` 中 `_CONCURRENCY` 模块常量改为函数参数 `max_concurrency`，默认值 10
- `dynamic_detector.py` 同步上述改动
- `max_rps` 参数语义从"硬性限制"改为"适配器建议值"，调用方仍可覆盖
- `state_scheduler.py` 启动检测时查询适配器速率建议值并传递到检测器
- 规格文档 SDPJDetector.md 第 291-320 行更新为与代码实现一致

## Capabilities

### New Capabilities

- `adapter-rate-limits`: 适配器配置驱动的 LLM 调用速率限制建议值，从适配器 JSON 配置读取，沿调用链传递到检测算法层

### Modified Capabilities

- `SDPJDetector`: 检测算法的并发控制参数从硬编码常量改为函数参数，接受适配器建议值

## Impact

- **代码变更**: `base.py`, `loader.py`, `adapter_engine.py`, `openai_adapter.py`, `anthropic_adapter.py`, `llm_adapter_lib.py`, `static_detector.py`, `dynamic_detector.py`, `sdpj_detector_interface.py`, `sdpj_detector/__init__.py`, `state_scheduler.py`
- **规格变更**: `openspec/specs/6.模块职责细化及技术细节/3.Execution Logic Layer/SDPJDetector.md` 第 291-320 行
- **向后兼容**: 适配器 JSON 配置中 `max_rps` 和 `max_concurrency` 为可选字段，不填则使用保守默认值，不影响已有配置
- **非破坏性变更**: 函数参数均有默认值，调用方无需立即修改
