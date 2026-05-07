## 1. 适配器层：增加速率限制字段

- [ ] 1.1 更新 `base.py` — LLMAdapter 构造函数增加 `max_rps=0.5` 和 `max_concurrency=3` 可选参数，`get_metadata()` 返回这两个字段
- [ ] 1.2 更新 `loader.py` — 从 config JSON 读取 `max_rps` 和 `max_concurrency`，传递给适配器构造函数
- [ ] 1.3 更新 `adapter_engine.py` — OpenAICompatibleAdapter 构造函数接收并存储 `max_rps`/`max_concurrency`，`get_metadata()` 返回这两个字段
- [ ] 1.4 更新 `openai_adapter.py` — OpenAIAdapter 透传 `max_rps`/`max_concurrency` 到父类
- [ ] 1.5 更新 `anthropic_adapter.py` — AnthropicAdapter 构造函数接收并存储 `max_rps`/`max_concurrency`，`get_metadata()` 返回这两个字段

## 2. 注册中心层：透传速率限制元信息

- [ ] 2.1 更新 `llm_adapter_lib.py` — `get_adapter_info()` 已通过 `adapter.get_metadata()` 透传，验证新字段可正常返回

## 3. 检测算法层：并发控制参数化

- [ ] 3.1 更新 `static_detector.py` — 删除 `_CONCURRENCY` 模块常量；`select_poc_pool()` 和 `run_static_detection()` 增加 `max_concurrency: int = 10` 参数；Semaphore 使用参数值；`max_rps` 默认值改为 5.0
- [ ] 3.2 更新 `dynamic_detector.py` — 删除对 `_CONCURRENCY` 的导入；`run_dynamic_detection()` 增加 `max_concurrency: int = 10` 参数；Semaphore 使用参数值；`max_rps` 默认值改为 5.0
- [ ] 3.3 更新 `sdpj_detector_interface.py` — SDPJDetectorInterface 的 `run_static_detection` 和 `run_dynamic_detection` 签名增加 `max_concurrency` 和 `max_rps` 参数
- [ ] 3.4 更新 `sdpj_detector/__init__.py` — SDPJDetector 类的 `run_static_detection` 和 `run_dynamic_detection` 签名增加 `max_concurrency` 和 `max_rps` 参数，透传到底层函数

## 4. 调度层：查询适配器速率并传递

- [ ] 4.1 更新 `state_scheduler.py` — `execute_detection_task()` 中查询适配器的 `max_rps`/`max_concurrency` 建议值，传递给 `SDPJDetector.run_static_detection()` 和 `run_dynamic_detection()`

## 5. 规格文档同步

- [ ] 5.1 更新 `SDPJDetector.md` 第 291-320 行 — RateLimiter 描述从"滑动窗口"改为"令牌桶"；参数默认值与代码一致（max_rps=5.0, _CONCURRENCY→max_concurrency=10, _BATCH_SIZE=100）；增加适配器配置驱动速率限制的说明
