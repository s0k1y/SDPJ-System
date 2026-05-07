# Tasks

## Task 1: 重写 RateLimiter 为令牌桶实现
- **文件**: `sdpj/infrastructure/utils/rate_limiter.py`
- **内容**: 用令牌桶算法替代互斥锁实现，保持 acquire() 接口不变
- **验证**: 单元测试验证并发 acquire() 不再串行

## Task 2: 动态检测并发化
- **文件**: `sdpj/core/sdpj_detector/dynamic_detector.py`
- **内容**: 引入 Semaphore + RateLimiter，将合规样本处理从串行改为 asyncio.gather 并发
- **验证**: 动态检测能并发执行，不再逐个串行等待

## Task 3: SampleDB 新增按风险类型批量查询样本
- **文件**: `sdpj/infrastructure/database/sample_db/sample_db.py`, `sdpj/infrastructure/database/sample_db/interface.py`
- **内容**: 新增 get_samples_by_risk_type 方法，使用 JOIN 查询替代 N+1
- **验证**: load_dataset_by_risk_type 只需1次查询

## Task 4: ResultDB 新增批量查询方法
- **文件**: `sdpj/infrastructure/database/result_db/result_db.py`, `sdpj/infrastructure/database/result_db/interface.py`
- **内容**: 新增 list_reports_by_group 和 list_result_data_by_reports 方法
- **验证**: aggregate_task_group_results 查询次数从 2N+2 降为 4

## Task 5: DataProcessor 使用新批量查询方法
- **文件**: `sdpj/drivers/data_processor.py`
- **内容**: load_dataset_by_risk_type 和 aggregate_task_group_results 改用批量查询
- **验证**: 功能不变，查询次数大幅减少

## Task 6: 运行测试验证
- **内容**: 运行现有单元测试和集成测试，确保所有功能正常
