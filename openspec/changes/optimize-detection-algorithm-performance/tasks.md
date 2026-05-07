## 1. 方案1：调整速率限制和并发参数

- [ ] 1.1 修改 static_detector.py 中 `_CONCURRENCY` 从 3 改为 10，`_BATCH_SIZE` 从 50 改为 100
- [ ] 1.2 修改 static_detector.py 中 `select_poc_pool` 和 `run_static_detection` 的 `max_rps` 默认值从 0.5 改为 2.0
- [ ] 1.3 修改 dynamic_detector.py 中 `run_dynamic_detection` 的 `RateLimiter(max_rps=0.5)` 改为 `RateLimiter(max_rps=2.0)`，并将 max_rps 作为函数参数暴露

## 2. 方案3：批量数据库操作

- [ ] 2.1 在 ResultDataRepository 中新增 `create_batch` 方法，使用 `session.add_all` + 单次 `flush` 批量写入
- [ ] 2.2 在 ResultDB 中新增 `append_result_data_batch` 方法，单次 session 中校验 report_id 存在性后批量写入
- [ ] 2.3 在 ResultDBInterface (Protocol) 中新增 `append_result_data_batch` 接口声明
- [ ] 2.4 在 DataProcessor 中新增 `append_result_data_batch` 方法，委托 ResultDB 批量写入
- [ ] 2.5 在 DataProcessorInterface (Protocol) 中新增 `append_result_data_batch` 接口声明
- [ ] 2.6 修改 static_detector.py 的 `run_static_detection` 中 `_process` 函数，收集批量结果后调用 `append_result_data_batch`
- [ ] 2.7 修改 dynamic_detector.py 的 `run_dynamic_detection`，收集批量结果后调用 `append_result_data_batch`

## 3. 方案5：异步化CPU密集型操作

- [ ] 3.1 在 sdpj/infrastructure/utils/ 下新增 cpu_executor.py，定义全局 ThreadPoolExecutor(max_workers=4) 和 `run_cpu()` 异步封装函数
- [ ] 3.2 在 static_detector.py 中新增 `_prepare_poc_async` 异步版本，对多模态构造和Base64编码调用 `run_cpu()`
- [ ] 3.3 修改 static_detector.py 的 `_check` 协程，将 `_prepare_poc` 替换为 `_prepare_poc_async`
- [ ] 3.4 修改 static_detector.py 的 `run_static_detection` 中 `_process` 函数，将 `_prepare_poc` 替换为 `_prepare_poc_async`
- [ ] 3.5 修改 dynamic_detector.py 的 `run_dynamic_detection`，将 `_prepare_poc` 替换为 `_prepare_poc_async`

## 4. 测试验证

- [ ] 4.1 运行现有单元测试，确保所有测试通过
- [ ] 4.2 运行集成测试，验证检测流程端到端正确性
